"""Re-run stage 01's 3-seed vision and text-only comparison, this time
recording exact-match by question category (total_count, shape_count,
presence, shape_color, column_shape) rather than only an aggregate number.

Mission 05's acceptance criteria require failure modes catalogued by
category, not just an aggregate accuracy -- stage 01's own `train.py` scores
and discards per-example detail, so this script exists to capture what that
one throws away. It imports `train_one`/`generate_answer` unmodified from
stage 01's `core/train.py` (same cross-mission-style import used throughout
this repository, here across stages of the same mission rather than across
missions) rather than re-deriving the training loop -- the only new code is
the per-category bookkeeping stage 01 had no reason to keep.

Same 3 seeds, same epochs/batch size as stage 01's reported run, so results
are directly comparable to `01-vision-fusion/runs/2026-07-31-vision-vs-text-only.md`.

Run:
    uv run --group torch python eval_by_category.py --seeds 3 --epochs 30 --batch-size 64
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import torch

STAGE01_CORE = Path(__file__).resolve().parents[2] / "01-vision-fusion" / "core"
sys.path.insert(0, str(STAGE01_CORE))
from tokenizer import Tokenizer
from train import DATA_DIR, generate_answer, load_jsonl, train_one
from vlm_model import Config

OUT_PATH = Path(__file__).resolve().parent.parent / "runs" / "category-breakdown.json"


def build_examples_with_type(raw: list[dict], tok: Tokenizer) -> list[dict]:
    """Same shape as stage 01's `build_examples`, plus the `type` field
    stage 01 never needed to keep."""
    out = []
    for ex in raw:
        pixels = torch.tensor(ex["pixels_rgb"], dtype=torch.float32)
        for qa in ex["qa"]:
            q_ids = tok.encode(qa["question"])
            a_ids = tok.encode(qa["answer"])
            text_ids = q_ids + [tok.sep_id] + a_ids + [tok.eos_id]
            answer_start = len(q_ids) + 1
            out.append(
                {"pixels": pixels, "text_ids": text_ids, "answer_start": answer_start, "type": qa["type"]}
            )
    return out


def evaluate_by_category(model, tok: Tokenizer, eval_examples: list[dict], device) -> dict[str, tuple[int, int]]:
    model.eval()
    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])  # [correct, total]
    for e in eval_examples:
        pixels = e["pixels"].to(device)
        answer_start = e["answer_start"]
        q_ids = e["text_ids"][: answer_start - 1]
        gt_answer = tok.decode(e["text_ids"][answer_start:-1])
        pred = generate_answer(model, tok, pixels, q_ids)
        tally[e["type"]][1] += 1
        if pred.strip() == gt_answer.strip():
            tally[e["type"]][0] += 1
    return {k: (v[0], v[1]) for k, v in tally.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=64)
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

    train_ex = [
        {"pixels": e["pixels"], "text_ids": e["text_ids"], "answer_start": e["answer_start"]}
        for e in build_examples_with_type(train_raw, tok)
    ]
    eval_ex = build_examples_with_type(eval_raw, tok)
    cfg = Config(vocab_size=len(tok))

    t0 = time.perf_counter()
    per_model: dict[str, list[dict[str, tuple[int, int]]]] = {"vision": [], "text_only": []}
    for use_vision, key in ((True, "vision"), (False, "text_only")):
        for seed in range(args.seeds):
            model, _ = train_one(cfg, use_vision, train_ex, seed, device, args.epochs, args.batch_size)
            tally = evaluate_by_category(model, tok, eval_ex, device)
            per_model[key].append(tally)
            print(f"[{key}] seed={seed} " + " ".join(f"{k}={v[0]}/{v[1]}" for k, v in sorted(tally.items())))
    elapsed = time.perf_counter() - t0

    # Sum correct/total across the 3 seeds per category (not averaged
    # per-seed accuracy) -- with ~150-200 eval examples per category this
    # keeps small-category denominators from being dominated by one seed's
    # noise the way an average-of-ratios would.
    summary: dict[str, dict[str, dict[str, int]]] = {}
    for key, tallies in per_model.items():
        combined: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for tally in tallies:
            for cat, (c, t) in tally.items():
                combined[cat][0] += c
                combined[cat][1] += t
        summary[key] = {cat: {"correct": c, "total": t} for cat, (c, t) in sorted(combined.items())}

    out = {"seeds": args.seeds, "epochs": args.epochs, "batch_size": args.batch_size, "wall_clock_s": elapsed, "by_category": summary}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2))
    print(f"wall-clock: {elapsed:.1f}s")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
