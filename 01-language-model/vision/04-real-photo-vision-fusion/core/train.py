"""Retrain stage 01's exact vision pathway and text-only baseline on real
COCO photographs (stage 03's data) instead of synthetic shapes.

Per mission.yaml's stages 03-05 extension, the model does not change --
`VisionLanguageTransformer`, `Config`, and `Tokenizer` are imported directly
from stage 01 (`sys.path.insert`, this repository's cross-mission reuse
convention, not a copy). Only the data source changes: `DATA_DIR` points at
stage 03's real-photo `train.jsonl`/`eval.jsonl` instead of stage 00's
synthetic manifests. `build_examples`/`make_batch`/`generate_answer`/
`evaluate`/`train_one` are stage 01's own functions, imported unchanged --
this file's only new code is the entry point and the declared-ceiling check
mission.yaml's cost_budget requires for these stages.

Run:
    uv run --group torch python train.py --seeds 3
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

STAGE01_CORE = Path(__file__).resolve().parents[2] / "01-vision-fusion" / "core"
sys.path.insert(0, str(STAGE01_CORE))
from tokenizer import Tokenizer
from train import (
    build_examples,
    evaluate,
    load_jsonl,
    train_one,
)
from vlm_model import Config

DATA_DIR = Path(__file__).resolve().parents[2] / "03-real-photo-task" / "data" / "raw"
CEILING_S = 30 * 60  # mission.yaml's stages 03-05 declared 30-minute ceiling


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--out", type=Path, default=Path("../runs"))
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
    print(f"vocab size: {len(tok)}")
    print(f"train qa pairs: {len(train_ex)}  eval qa pairs: {len(eval_ex)}")

    results: dict[str, list[float]] = {"vision": [], "text_only": []}
    losses: dict[str, list[float]] = {"vision": [], "text_only": []}
    t0 = time.perf_counter()
    ceiling_hit = False
    for use_vision, key in ((True, "vision"), (False, "text_only")):
        n_params = None
        for seed in range(args.seeds):
            elapsed_so_far = time.perf_counter() - t0
            if elapsed_so_far > CEILING_S:
                print(f"CEILING_EXCEEDED at {elapsed_so_far:.1f}s (30-minute ceiling) -- stopping, not shrinking")
                ceiling_hit = True
                break
            model, last_loss = train_one(cfg, use_vision, train_ex, seed, device, args.epochs, args.batch_size)
            if n_params is None:
                n_params = sum(p.numel() for p in model.parameters())
            acc = evaluate(model, tok, eval_ex, device)
            results[key].append(acc)
            losses[key].append(last_loss)
            print(f"[{key}] seed={seed} final_train_loss={last_loss:.4f} eval_exact_match={acc:.4f}")
        if ceiling_hit:
            break
        print(f"[{key}] param count: {n_params:,}")
    elapsed = time.perf_counter() - t0

    def summarize(xs: list[float]) -> str:
        if not xs:
            return "no seeds completed"
        mean = sum(xs) / len(xs)
        spread = max(xs) - min(xs) if len(xs) > 1 else 0.0
        return f"mean={mean:.4f} spread={spread:.4f} per_seed={[round(x, 4) for x in xs]}"

    print("\n=== SUMMARY ===")
    print(f"wall-clock: {elapsed:.1f}s  device: {device}  ceiling_hit: {ceiling_hit}")
    print(f"vision     eval exact-match: {summarize(results['vision'])}")
    print(f"text_only  eval exact-match: {summarize(results['text_only'])}")

    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "real-photo-results.json").write_text(
        json.dumps(
            {
                "vision_per_seed": results["vision"],
                "text_only_per_seed": results["text_only"],
                "wall_clock_s": elapsed,
                "ceiling_s": CEILING_S,
                "ceiling_hit": ceiling_hit,
                "vocab_size": len(tok),
                "train_qa_pairs": len(train_ex),
                "eval_qa_pairs": len(eval_ex),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
