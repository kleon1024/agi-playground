"""Instrument a real training loop with real per-step timing, then compute
p50/p95 from the samples actually collected -- never a single average.

Reuses mission 01's Config/Transformer unmodified
(missions/01-language-model-agent/02-pretrain/core/model.py) rather than
reimplementing a toy model, per this repository's cross-lesson reuse
convention. No line of model.py is changed; this file only wraps its
training step with a stopwatch and a counter.

Run:  python instrumented_train.py --steps 200 --out ../runs
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

_MODEL_DIR = (
    Path(__file__).resolve().parents[3]
    / "missions"
    / "01-language-model-agent"
    / "02-pretrain"
    / "core"
)
sys.path.insert(0, str(_MODEL_DIR))
from model import Config, Transformer


def percentile(sorted_values: list[float], pct: float) -> float:
    """Nearest-rank percentile over an already-sorted list of real samples."""
    if not sorted_values:
        raise ValueError("no samples")
    k = max(0, min(len(sorted_values) - 1, round(pct / 100 * (len(sorted_values) - 1))))
    return sorted_values[k]


def histogram(values: list[float], n_buckets: int = 8) -> list[dict]:
    lo, hi = min(values), max(values)
    width = (hi - lo) / n_buckets if hi > lo else 1.0
    counts = [0] * n_buckets
    for v in values:
        idx = min(n_buckets - 1, int((v - lo) / width))
        counts[idx] += 1
    return [
        {"bucket_start_s": round(lo + i * width, 5), "count": counts[i]}
        for i in range(n_buckets)
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seq-len", type=int, default=64)
    parser.add_argument("--out", type=Path, default=Path("runs"))
    args = parser.parse_args()

    torch.manual_seed(0)
    cfg = Config(vocab_size=512, n_layer=2, n_head=4, n_kv_head=2, d_model=128, d_ff=256, block_size=args.seq_len)
    model = Transformer(cfg)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)

    step_times: list[float] = []
    counters = {"steps": 0, "tokens": 0}

    # A handful of unmeasured warmup steps -- same reason infra/03-orchestration
    # needs one: the first few steps pay one-time cost (lazy CUDA/BLAS init,
    # Python attribute-lookup caching) that has nothing to do with steady-
    # state per-step latency and would otherwise inflate p95 on nothing.
    for _ in range(5):
        idx = torch.randint(0, cfg.vocab_size, (args.batch_size, args.seq_len))
        targets = torch.randint(0, cfg.vocab_size, (args.batch_size, args.seq_len))
        _, loss = model(idx, targets)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

    for _ in range(args.steps):
        idx = torch.randint(0, cfg.vocab_size, (args.batch_size, args.seq_len))
        targets = torch.randint(0, cfg.vocab_size, (args.batch_size, args.seq_len))

        t0 = time.perf_counter()
        _, loss = model(idx, targets)
        loss.backward()
        optimizer.step()
        optimizer.zero_grad()
        t1 = time.perf_counter()

        step_times.append(t1 - t0)
        counters["steps"] += 1
        counters["tokens"] += idx.numel()

    sorted_times = sorted(step_times)
    result = {
        "config": {"steps": args.steps, "batch_size": args.batch_size, "seq_len": args.seq_len},
        "counters": counters,
        "final_loss": loss.item(),
        "step_time_s": {
            "p50": percentile(sorted_times, 50),
            "p95": percentile(sorted_times, 95),
            "min": sorted_times[0],
            "max": sorted_times[-1],
            "mean": sum(sorted_times) / len(sorted_times),
        },
        "step_time_histogram": histogram(step_times),
    }

    print(f"steps={counters['steps']} tokens={counters['tokens']} final_loss={result['final_loss']:.4f}")
    print(f"step time p50={result['step_time_s']['p50']*1000:.2f}ms p95={result['step_time_s']['p95']*1000:.2f}ms")
    print("histogram (step-time buckets, count):")
    for b in result["step_time_histogram"]:
        print(f"  {b['bucket_start_s']*1000:7.2f}ms : {'#' * b['count']} ({b['count']})")

    args.out.mkdir(parents=True, exist_ok=True)
    out_file = args.out / "instrumented-train-result.json"
    out_file.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {out_file}")


if __name__ == "__main__":
    main()
