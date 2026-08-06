"""The cost-quality knee, read from the recorded tier run.

Stage 03's run resolved every attempt at every tier, so resolve rate
separates nothing and the cost per attempt is the differentiator. This
script reads the recorded JSONL and lays out the per-tier cost and wall-
clock, so the knee (where a cheaper tier stops being worth the latency)
is a table.

Input (recorded, unchanged): ../runs/2026-07-29-results.jsonl

Run:
    uv run python core/knee_read.py
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path


def main() -> None:
    rows = [
        json.loads(line)
        for line in (
            Path(__file__).resolve().parents[2] / "runs" / "2026-07-29-results.jsonl"
        ).read_text().splitlines()
        if line.strip()
    ]
    per_tier: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        per_tier[r["model"]].append(r)
    print("model-tier costs (recorded), read:")
    print(f"  {'tier':<7} {'$/attempt':>10} {'median wall-clock':>18} {'turns':>6}")
    for tier, attempts in sorted(per_tier.items()):
        cost = statistics.fmean(a.get("cost_usd", 0) for a in attempts)
        wall = statistics.median(a.get("wall_clock_s", 0) for a in attempts)
        turns = statistics.fmean(a.get("turns", 0) for a in attempts)
        print(f"  {tier:<7} {cost:>10.4f} {wall:>18.1f} {turns:>6.1f}")
    print("\nreading: every tier resolved everything, so the choice is cost and")
    print("latency — and the run's own probe on the patches is what makes the")
    print("tiers comparable rather than all-equal.")


if __name__ == "__main__":
    main()
