"""Deterministic speculative decoding: a small draft model proposes several
tokens autoregressively, a larger target model checks all of them in one
batched forward pass, and the walk accepts every proposed token up to the
first place the target's own greedy choice disagrees.

This is the greedy special case of Leviathan, Kalman & Matias, "Fast
Inference from Transformers via Speculative Decoding" (Google, 2023) and
Chen et al., "Accelerating Large Language Model Decoding with Speculative
Sampling" (DeepMind, 2023) -- both papers verify with probabilistic
rejection sampling so the *distribution* stays exact under temperature > 0
sampling. Greedy decoding only ever wants the argmax, so the harder
rejection-sampling machinery collapses to a single equality check per
position: accept a proposed token iff it equals what the target's own
forward pass would have produced there anyway. That makes correctness
trivial to verify by direct comparison against plain target-only greedy
decoding (see `verify_correctness` below) rather than only approximately
true in distribution -- the scope this chapter claims, and no more.

No CUDA GPU is available in this environment (see runs/ for the check), so
unlike `01-graph-execution` and `02-quantization` this chapter trains its
own tiny draft and target models from scratch on the local CPU lane, on the
same tinyshakespeare corpus foundations/01-first-training-loop uses, rather
than reusing missions/01's 88M-parameter checkpoint. The point under test --
whether a cheap model's guesses save a expensive model's forward passes --
does not depend on either model being good at Shakespeare, only on both
being trained on the same distribution.
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "01-language-model/05-serve/core"))
sys.path.insert(0, str(ROOT / "01-language-model/02-pretrain/core"))
from engine import generate_naive
from model import Config, Transformer

DEVICE = "cpu"  # honest: torch.cuda.is_available() is False in this environment
DATA_URL = "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
DATA_PATH = Path(__file__).resolve().parent / "data" / "cache" / "shakespeare.txt"


def load_corpus() -> str:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        urllib.request.urlretrieve(DATA_URL, DATA_PATH)
    return DATA_PATH.read_text()


def build_tokenizer(text: str):
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    itos = {i: c for c, i in stoi.items()}
    encode = lambda s: [stoi[c] for c in s]
    decode = lambda ids: "".join(itos[i] for i in ids)
    return len(chars), encode, decode


def get_batch(data: torch.Tensor, block: int, batch: int, rng: torch.Generator):
    ix = torch.randint(len(data) - block - 1, (batch,), generator=rng)
    x = torch.stack([data[i : i + block] for i in ix])
    y = torch.stack([data[i + 1 : i + block + 1] for i in ix])
    return x, y


def train(model: Transformer, data: torch.Tensor, block: int, batch: int, steps: int, lr: float, seed: int, label: str) -> float:
    gen = torch.Generator().manual_seed(seed)
    torch.manual_seed(seed)
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    model.train()
    t0 = time.perf_counter()
    for step in range(steps):
        x, y = get_batch(data, block, batch, gen)
        _, loss = model(x, y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if step % max(1, steps // 4) == 0 or step == steps - 1:
            print(f"  [{label}] step {step:4d}/{steps}  loss {loss.item():.4f}")
    model.eval()
    return time.perf_counter() - t0


@torch.no_grad()
def draft_propose(draft: Transformer, idx: torch.Tensor, k: int) -> list[int]:
    cur = idx
    proposals = []
    for _ in range(k):
        logits, _ = draft(cur)
        nxt = int(logits[0, -1].argmax())
        proposals.append(nxt)
        cur = torch.cat([cur, torch.tensor([[nxt]])], dim=1)
    return proposals


@torch.no_grad()
def speculative_decode(target: Transformer, draft: Transformer, prompt_ids: list[int], n_tokens: int, k: int):
    """Greedy speculative decoding. Returns (generated_ids, per_round_accept_counts).

    Each round: the draft proposes `k` tokens one at a time (its own
    autoregressive loop, full recompute -- draft is tiny, no cache needed at
    this scale). The target then runs exactly ONE forward pass over
    prompt-so-far + all k proposals and reads off its own greedy argmax at
    every one of those k positions in that same pass. Accept proposals up to
    the first position where the target disagrees; substitute the target's
    own token there. If every proposal is accepted, the same forward pass
    already priced in a free bonus token past the last proposal.
    """
    idx = torch.tensor([prompt_ids], dtype=torch.long)
    generated = 0
    rounds = []
    while generated < n_tokens:
        k_this = min(k, n_tokens - generated)
        proposals = draft_propose(draft, idx, k_this)
        candidate = torch.cat([idx, torch.tensor([proposals])], dim=1)
        logits, _ = target(candidate)
        base = idx.shape[1] - 1  # logits[base] predicts candidate's first proposed token
        accepted = 0
        for i in range(k_this):
            if int(logits[0, base + i].argmax()) == proposals[i]:
                accepted += 1
            else:
                break
        rounds.append((accepted, k_this))
        if accepted:
            idx = torch.cat([idx, torch.tensor([proposals[:accepted]])], dim=1)
            generated += accepted
        if accepted < k_this:
            correction = int(logits[0, base + accepted].argmax())
            idx = torch.cat([idx, torch.tensor([[correction]])], dim=1)
            generated += 1
        elif generated < n_tokens:
            bonus = int(logits[0, base + k_this].argmax())
            idx = torch.cat([idx, torch.tensor([[bonus]])], dim=1)
            generated += 1
    return idx[0].tolist(), rounds


def verify_correctness(target: Transformer, draft: Transformer, prompt_ids: list[int], n_tokens: int, k: int) -> bool:
    baseline = generate_naive(target, prompt_ids, n_tokens, DEVICE)
    spec, _ = speculative_decode(target, draft, prompt_ids, n_tokens, k)
    return baseline == spec


def bench(label: str, fn, *args) -> tuple[float, Any]:
    print(f"  running {label}...")
    t0 = time.perf_counter()
    result = fn(*args)
    return time.perf_counter() - t0, result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-steps", type=int, default=600)
    ap.add_argument("--draft-good-steps", type=int, default=600)
    ap.add_argument("--draft-poor-steps", type=int, default=40)
    ap.add_argument("--block", type=int, default=128)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--gen-tokens", type=int, default=200)
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1337)
    args = ap.parse_args()
    torch.manual_seed(args.seed)  # covers model init; train() reseeds per-model for its own batch sampling

    text = load_corpus()
    vocab_size, encode, decode = build_tokenizer(text)
    data = torch.tensor(encode(text), dtype=torch.long)

    target_cfg = Config(vocab_size=vocab_size, n_layer=4, n_head=4, n_kv_head=2, d_model=256, d_ff=683, block_size=args.block)
    draft_cfg = Config(vocab_size=vocab_size, n_layer=2, n_head=2, n_kv_head=2, d_model=96, d_ff=256, block_size=args.block)

    target = Transformer(target_cfg)
    draft_good = Transformer(draft_cfg)
    draft_poor = Transformer(draft_cfg)

    print(f"target:     {target.param_report()}")
    print(f"draft:      {draft_good.param_report()}")
    print()

    print("training target...")
    t_target_train = train(target, data, args.block, args.batch, args.target_steps, 3e-4, args.seed, "target")
    print(f"  target train wall-clock: {t_target_train:.2f}s\n")

    print("training draft (good, well-trained)...")
    t_good_train = train(draft_good, data, args.block, args.batch, args.draft_good_steps, 3e-4, args.seed + 1, "draft-good")
    print(f"  draft-good train wall-clock: {t_good_train:.2f}s\n")

    print("training draft (poor, undertrained)...")
    t_poor_train = train(draft_poor, data, args.block, args.batch, args.draft_poor_steps, 3e-4, args.seed + 2, "draft-poor")
    print(f"  draft-poor train wall-clock: {t_poor_train:.2f}s\n")

    prompt = "ROMEO:"
    prompt_ids = encode(prompt)

    print("verifying: does speculative output exactly match plain target-only greedy decoding?")
    ok_good = verify_correctness(target, draft_good, prompt_ids, args.gen_tokens, args.k)
    ok_poor = verify_correctness(target, draft_poor, prompt_ids, args.gen_tokens, args.k)
    print(f"  exact match with draft-good: {ok_good}")
    print(f"  exact match with draft-poor: {ok_poor}\n")
    assert ok_good and ok_poor, "speculative decode diverged from plain greedy decode"

    print(f"benchmarking {args.gen_tokens} generated tokens, k={args.k}, prompt={prompt!r}")
    t_baseline, baseline_ids = bench("baseline", generate_naive, target, prompt_ids, args.gen_tokens, DEVICE)
    t_good, (_good_ids, good_rounds) = bench("good", speculative_decode, target, draft_good, prompt_ids, args.gen_tokens, args.k)
    t_poor, (_poor_ids, poor_rounds) = bench("poor", speculative_decode, target, draft_poor, prompt_ids, args.gen_tokens, args.k)

    def summarize(rounds):
        accepted = sum(a for a, _ in rounds)
        proposed = sum(k_ for _, k_ in rounds)
        return accepted, len(rounds), accepted / proposed if proposed else 0.0

    good_acc, good_n_rounds, good_rate = summarize(good_rounds)
    poor_acc, poor_n_rounds, poor_rate = summarize(poor_rounds)

    print()
    print(f"{'config':>12} {'wall_s':>8} {'vs_baseline':>12} {'accept_rate':>12} {'accepted/round':>15} {'rounds':>7}")
    print(f"{'baseline':>12} {t_baseline:>8.3f} {1.0:>12.2f} {'--':>12} {'--':>15} {(args.gen_tokens):>7}")
    print(f"{'draft-good':>12} {t_good:>8.3f} {t_baseline / t_good:>12.2f} {good_rate:>12.3f} {good_acc / good_n_rounds:>15.2f} {good_n_rounds:>7}")
    print(f"{'draft-poor':>12} {t_poor:>8.3f} {t_baseline / t_poor:>12.2f} {poor_rate:>12.3f} {poor_acc / poor_n_rounds:>15.2f} {poor_n_rounds:>7}")

    print()
    print("sample completion (target-only baseline):")
    print(decode(baseline_ids))


if __name__ == "__main__":
    main()
