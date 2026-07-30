"""Train and evaluate the vision pathway against the text-only baseline.

Both models are the identical `VisionLanguageTransformer` class and Config --
the only difference is `use_vision`, which is exactly the one variable
mission 05's mission.yaml requires isolating. Loss is masked to answer tokens
only (mission 01 stage 03's `-100`/`ignore_index` convention, adapted to this
stage's own tokenizer and mask). Evaluation is greedy decode of the answer,
compared by exact string match against the ground-truth answer -- the
`primary_metric` mission.yaml declares.

Run:
    uv run --group torch python train.py --seeds 3
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tokenizer import Tokenizer
from vlm_model import Config, VisionLanguageTransformer

DATA_DIR = Path(__file__).resolve().parents[2] / "00-image-caption-task" / "data" / "raw"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def build_examples(raw: list[dict], tok: Tokenizer) -> list[dict]:
    out = []
    for ex in raw:
        pixels = torch.tensor(ex["pixels_rgb"], dtype=torch.float32)  # (1024, 3)
        for qa in ex["qa"]:
            q_ids = tok.encode(qa["question"])
            a_ids = tok.encode(qa["answer"])
            text_ids = q_ids + [tok.sep_id] + a_ids + [tok.eos_id]
            answer_start = len(q_ids) + 1  # index of first answer token in text_ids
            out.append({"pixels": pixels, "text_ids": text_ids, "answer_start": answer_start})
    return out


def make_batch(examples: list[dict], max_input_len: int, device) -> dict:
    B = len(examples)
    pixels = torch.stack([e["pixels"] for e in examples]).to(device)
    text_in = torch.zeros(B, max_input_len, dtype=torch.long, device=device)  # pad_id == 0
    targets = torch.full((B, max_input_len), -100, dtype=torch.long, device=device)
    valid_lens = torch.zeros(B, dtype=torch.long, device=device)
    for i, e in enumerate(examples):
        ids = e["text_ids"]
        inp = ids[:-1]
        tgt = ids[1:]
        L = len(inp)
        valid_lens[i] = L
        text_in[i, :L] = torch.tensor(inp, dtype=torch.long)
        for j, next_tok in enumerate(tgt):
            # predicting position (answer_start-1) reproduces the SEP token
            # itself, which is a fixed, deterministic prediction independent
            # of the answer -- excluded so loss reflects only the genuinely
            # answer-dependent tokens (answer words + EOS).
            if j + 1 >= e["answer_start"]:
                targets[i, j] = next_tok
    return {"pixels": pixels, "text_in": text_in, "valid_lens": valid_lens, "targets": targets}


@torch.no_grad()
def generate_answer(model, tok: Tokenizer, pixels: torch.Tensor, q_ids: list[int], max_new: int = 6) -> str:
    device = pixels.device
    seq = list(q_ids) + [tok.sep_id]
    for _ in range(max_new):
        text_in = torch.tensor([seq], dtype=torch.long, device=device)
        valid_lens = torch.tensor([len(seq)], device=device)
        px = pixels.unsqueeze(0) if model.use_vision else None
        logits, _ = model(px, text_in, valid_lens)
        next_id = int(logits[0, -1].argmax())
        if next_id == tok.eos_id:
            break
        seq.append(next_id)
    sep_pos = seq.index(tok.sep_id)
    return tok.decode(seq[sep_pos + 1 :])


def evaluate(model, tok: Tokenizer, eval_examples: list[dict], device) -> float:
    model.eval()
    correct = 0
    for e in eval_examples:
        pixels = e["pixels"].to(device)
        answer_start = e["answer_start"]
        q_ids = e["text_ids"][: answer_start - 1]  # up to (not including) SEP
        gt_answer = tok.decode(e["text_ids"][answer_start:-1])  # exclude EOS
        pred = generate_answer(model, tok, pixels, q_ids)
        if pred.strip() == gt_answer.strip():
            correct += 1
    return correct / len(eval_examples)


def train_one(cfg: Config, use_vision: bool, train_ex: list[dict], seed: int, device, epochs: int, batch_size: int):
    torch.manual_seed(seed)
    rng = random.Random(seed)
    model = VisionLanguageTransformer(cfg, use_vision=use_vision).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3)
    max_input_len = max(len(e["text_ids"]) - 1 for e in train_ex)
    order = list(range(len(train_ex)))
    last_loss = 0.0
    for _ in range(epochs):
        rng.shuffle(order)
        for start in range(0, len(order), batch_size):
            idxs = order[start : start + batch_size]
            batch_examples = [train_ex[i] for i in idxs]
            batch = make_batch(batch_examples, max_input_len, device)
            model.train()
            _, loss = model(
                batch["pixels"] if use_vision else None, batch["text_in"], batch["valid_lens"], batch["targets"]
            )
            opt.zero_grad()
            loss.backward()
            opt.step()
            last_loss = loss.item()
    return model, last_loss


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--out", type=Path, default=Path("../runs"))
    ap.add_argument(
        "--show-examples", type=int, default=0, help="print N real eval predictions from seed 0 of each model"
    )
    args = ap.parse_args()

    device = torch.device("cpu")
    train_raw = load_jsonl(DATA_DIR / "train.jsonl")
    eval_raw = load_jsonl(DATA_DIR / "eval.jsonl")

    all_text = []
    for split in (train_raw, eval_raw):
        for ex in split:
            for qa in ex["qa"]:
                all_text.append(qa["question"])
                all_text.append(qa["answer"])
    tok = Tokenizer.build(all_text)
    tok.save(Path(__file__).resolve().parent / "vocab.json")

    train_ex = build_examples(train_raw, tok)
    eval_ex = build_examples(eval_raw, tok)

    cfg = Config(vocab_size=len(tok))
    print(f"vocab size: {len(tok)}  words: {tok.vocab}")
    print(f"train qa pairs: {len(train_ex)}  eval qa pairs: {len(eval_ex)}")

    results: dict[str, list[float]] = {"vision": [], "text_only": []}
    losses: dict[str, list[float]] = {"vision": [], "text_only": []}
    t0 = time.perf_counter()
    for use_vision, key in ((True, "vision"), (False, "text_only")):
        n_params = None
        for seed in range(args.seeds):
            model, last_loss = train_one(
                cfg, use_vision, train_ex, seed, device, args.epochs, args.batch_size
            )
            if n_params is None:
                n_params = sum(p.numel() for p in model.parameters())
            acc = evaluate(model, tok, eval_ex, device)
            results[key].append(acc)
            losses[key].append(last_loss)
            print(f"[{key}] seed={seed} final_train_loss={last_loss:.4f} eval_exact_match={acc:.4f}")
            if seed == 0 and args.show_examples:
                model.eval()
                print(f"[{key}] {args.show_examples} real held-out predictions (seed 0):")
                for e in eval_ex[: args.show_examples]:
                    answer_start = e["answer_start"]
                    q_ids = e["text_ids"][: answer_start - 1]
                    gt = tok.decode(e["text_ids"][answer_start:-1])
                    pred = generate_answer(model, tok, e["pixels"], q_ids)
                    q_text = tok.decode(q_ids)
                    print(f"    Q: {q_text}  GT: {gt!r}  pred: {pred!r}")
        print(f"[{key}] param count: {n_params:,}")
    elapsed = time.perf_counter() - t0

    def summarize(xs: list[float]) -> str:
        mean = sum(xs) / len(xs)
        spread = max(xs) - min(xs)
        return f"mean={mean:.4f} spread={spread:.4f} per_seed={[round(x, 4) for x in xs]}"

    print("\n=== SUMMARY ===")
    print(f"wall-clock: {elapsed:.1f}s  device: {device}")
    print(f"vision     eval exact-match: {summarize(results['vision'])}")
    print(f"text_only  eval exact-match: {summarize(results['text_only'])}")
    print(f"vision     final train loss: {summarize(losses['vision'])}")
    print(f"text_only  final train loss: {summarize(losses['text_only'])}")


if __name__ == "__main__":
    main()
