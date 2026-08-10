"""Deterministic early-exit cascade: a cheap model answers every step it is
confident about, and only low-confidence steps are escalated to an expensive
model. The question is where that gate stops paying.

This is the inference-side cousin of the sibling chapter's speculative
decoding: there the expensive model *verifies* every cheap proposal; here the
cheap model's own confidence *decides* whether the expensive model is called
at all. The classic formulation is BranchyNet (Teerapittayanon et al., ICPR
2016; arXiv:1709.01686), which branches early exits off a network and gates
them on a confidence threshold. The failure mode this chapter measures is the
gate itself: set the threshold against the wrong model quality and the
cascade either escalates everything (pays cheap + expensive per step, so it
is slower than the expensive model alone) or accepts garbage (a
confidently-wrong cheap model passes bad tokens through with no check).

No CUDA GPU is available in this environment, so — exactly like
`speculative-decoding` — this chapter trains its own tiny models from scratch
on the local CPU lane, on the same tinyshakespeare corpus
`foundations/first-training-loop` uses. `target` is the expensive model;
`cheap-good` and `cheap-poor` share one architecture and differ only in
training steps (600 vs 40), isolating cheap-model *quality* as the variable
under test while holding the gate mechanism, the target, and the prompt fixed.

Run:  uv run --group torch python3 cascade.py
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request
from pathlib import Path

import torch
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "01-language-model/pretrain/core"))
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


def train(
    model: Transformer,
    data: torch.Tensor,
    block: int,
    batch: int,
    steps: int,
    lr: float,
    seed: int,
    label: str,
) -> float:
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
def greedy(model: Transformer, prompt_ids: list[int], n_tokens: int) -> list[int]:
    """Plain autoregressive greedy decoding, target or cheap, no gate."""
    idx = torch.tensor([prompt_ids], dtype=torch.long)
    generated = []
    for _ in range(n_tokens):
        logits, _ = model(idx)
        nxt = int(logits[0, -1].argmax())
        generated.append(nxt)
        idx = torch.cat([idx, torch.tensor([[nxt]])], dim=1)
    return generated


@torch.no_grad()
def confidence(model: Transformer, idx: torch.Tensor) -> float:
    """Max softmax probability of the model's next-token call."""
    logits, _ = model(idx)
    probs = F.softmax(logits[0, -1], dim=-1)
    return float(probs.max())


@torch.no_grad()
def cascade_decode(
    target: Transformer,
    cheap: Transformer,
    prompt_ids: list[int],
    n_tokens: int,
    tau: float,
    budget: int | None,
) -> tuple[list[int], dict]:
    """Early-exit cascade with a confidence gate and an optional expensive-call
    budget.

    Each step: the cheap model proposes a token and a confidence. If the
    confidence clears `tau`, the cheap token is emitted (cheap forward only).
    Otherwise the target is called and its argmax is emitted (cheap forward +
    target forward). `budget` caps how many target calls a sequence may make;
    once exhausted, every remaining step is emitted cheap, gated or not --
    the latency-budget fallback a serving system actually implements.
    """
    idx = torch.tensor([prompt_ids], dtype=torch.long)
    expensive = 0
    accepted_cheap = 0
    forced_cheap = 0
    for _ in range(n_tokens):
        cheap_logits, _ = cheap(idx)
        cheap_tok = int(cheap_logits[0, -1].argmax())
        conf = float(F.softmax(cheap_logits[0, -1], dim=-1).max())
        escalate = conf < tau
        if escalate and (budget is None or expensive < budget):
            target_logits, _ = target(idx)
            tok = int(target_logits[0, -1].argmax())
            expensive += 1
        else:
            tok = cheap_tok
            accepted_cheap += 1
            if escalate:  # wanted the target, but the budget said no
                forced_cheap += 1
        idx = torch.cat([idx, torch.tensor([[tok]])], dim=1)
    return idx[0].tolist()[len(prompt_ids) :], {
        "expensive_calls": expensive,
        "accepted_cheap": accepted_cheap,
        "forced_cheap": forced_cheap,
        "steps": n_tokens,
    }


@torch.no_grad()
def target_ce(target: Transformer, prompt_ids: list[int], generated: list[int]) -> float:
    """Average target cross-entropy over the generated tokens: how much the
    expensive model dislikes the output it was not asked to produce."""
    idx = torch.tensor([prompt_ids], dtype=torch.long)
    total, n = 0.0, 0
    for tok in generated:
        logits, _ = target(idx)
        total += F.cross_entropy(logits[0, -1], torch.tensor(tok)).item()
        idx = torch.cat([idx, torch.tensor([[tok]])], dim=1)
        n += 1
    return total / n


def exact_match(reference: list[int], generated: list[int]) -> float:
    return sum(a == b for a, b in zip(reference, generated)) / len(reference)


def bench(label: str, fn, *args) -> tuple[float, tuple]:
    print(f"  running {label}...")
    t0 = time.perf_counter()
    result = fn(*args)
    return time.perf_counter() - t0, result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-steps", type=int, default=600)
    ap.add_argument("--cheap-good-steps", type=int, default=600)
    ap.add_argument("--cheap-poor-steps", type=int, default=40)
    ap.add_argument("--block", type=int, default=128)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--gen-tokens", type=int, default=100)
    ap.add_argument("--seed", type=int, default=1337)
    args = ap.parse_args()
    torch.manual_seed(args.seed)

    text = load_corpus()
    vocab_size, encode, decode = build_tokenizer(text)
    data = torch.tensor(encode(text), dtype=torch.long)

    target_cfg = Config(
        vocab_size=vocab_size, n_layer=4, n_head=4, n_kv_head=2,
        d_model=256, d_ff=683, block_size=args.block,
    )
    cheap_cfg = Config(
        vocab_size=vocab_size, n_layer=2, n_head=2, n_kv_head=2,
        d_model=96, d_ff=256, block_size=args.block,
    )

    target = Transformer(target_cfg)
    cheap_good = Transformer(cheap_cfg)
    cheap_poor = Transformer(cheap_cfg)
    print(f"target (expensive):   {target.param_report()}")
    print(f"cheap:                {cheap_good.param_report()}")
    print()

    print("training target...")
    t_target = train(target, data, args.block, args.batch, args.target_steps, 3e-4, args.seed, "target")
    print(f"  target train wall-clock: {t_target:.2f}s\n")
    print("training cheap (good, well-trained)...")
    t_good = train(cheap_good, data, args.block, args.batch, args.cheap_good_steps, 3e-4, args.seed + 1, "cheap-good")
    print(f"  cheap-good train wall-clock: {t_good:.2f}s\n")
    print("training cheap (poor, undertrained)...")
    t_poor = train(cheap_poor, data, args.block, args.batch, args.cheap_poor_steps, 3e-4, args.seed + 2, "cheap-poor")
    print(f"  cheap-poor train wall-clock: {t_poor:.2f}s\n")

    prompt = "ROMEO:"
    prompt_ids = encode(prompt)
    n = args.gen_tokens

    print(f"benchmarking {n} generated tokens from prompt {prompt!r}\n")
    t_baseline, baseline_ids = bench("target-only", greedy, target, prompt_ids, n)
    t_cheap, cheap_good_ids = bench("cheap-only (good)", greedy, cheap_good, prompt_ids, n)
    t_cheap_poor, cheap_poor_ids = bench("cheap-only (poor)", greedy, cheap_poor, prompt_ids, n)

    def run_cascade(label, cheap, tau, budget=None):
        t, (ids, stats) = bench(
            label, cascade_decode, target, cheap, prompt_ids, n, tau, budget
        )
        ce = target_ce(target, prompt_ids, ids)
        match = exact_match(baseline_ids, ids)
        return t, stats, ce, match, ids

    rows = []
    rows.append(("target-only", t_baseline, None, target_ce(target, prompt_ids, baseline_ids), 1.0))
    rows.append(("cheap-only (good)", t_cheap, None, target_ce(target, prompt_ids, cheap_good_ids), exact_match(baseline_ids, cheap_good_ids)))
    rows.append(("cheap-only (poor)", t_cheap_poor, None, target_ce(target, prompt_ids, cheap_poor_ids), exact_match(baseline_ids, cheap_poor_ids)))
    for tau in (0.3, 0.5, 0.7, 0.9):
        t, stats, ce, match, _ = run_cascade(f"cascade good tau={tau}", cheap_good, tau)
        rows.append((f"cascade good tau={tau}", t, stats, ce, match))
    t, stats, ce, match, _ = run_cascade("cascade poor tau=0.7", cheap_poor, 0.7)
    rows.append(("cascade poor tau=0.7", t, stats, ce, match))
    t, stats, ce, match, _ = run_cascade("cascade good tau=0.9 budget=5", cheap_good, 0.9, budget=5)
    rows.append(("cascade good tau=0.9 budget=5", t, stats, ce, match))

    print()
    hdr = (
        f"{'config':<28}{'wall_s':>8}{'vs target':>10}{'exp calls':>11}"
        f"{'accept%':>9}{'target CE':>10}{'match%':>8}"
    )
    print(hdr)
    print("-" * len(hdr))
    for label, wall, stats, ce, match in rows:
        exp = f"{stats['expensive_calls']}/{stats['steps']}" if stats else "--"
        acc = (
            f"{100 * stats['accepted_cheap'] / stats['steps']:.0f}"
            if stats else "--"
        )
        forced = (
            f" (forced {stats['forced_cheap']})"
            if stats and stats["forced_cheap"]
            else ""
        )
        print(
            f"{label:<28}{wall:>8.2f}{t_baseline / wall:>10.2f}{exp:>11}"
            f"{acc:>9}{ce:>10.3f}{100 * match:>8.1f}{forced}"
        )

    print()
    print("sample completion (target-only baseline):")
    print(decode(baseline_ids))


if __name__ == "__main__":
    main()
