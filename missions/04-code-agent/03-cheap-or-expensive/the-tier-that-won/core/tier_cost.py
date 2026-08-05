"""When every tier resolves everything, the cost split is the result.

Stage 03's recorded run resolved all 18 tasks across all three tiers —
haiku, sonnet, opus at 6/6 each — so the resolve rate separates nothing.
The question the stage was built for is then purely economic: at what
fraction of the cost, tokens, turns, and wall-clock did the cheap tier do
the same job? This script reads the recorded results and lays out the
per-tier economics.

Input (recorded, unchanged): ../../03-cheap-or-expensive/runs/2026-07-29-results.jsonl

Run:
    uv run python core/tier_cost.py
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path


def main() -> None:
    path = Path(__file__).resolve().parents[3] / "03-cheap-or-expensive" / "runs" / "2026-07-29-results.jsonl"
    with open(path) as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    by_tier: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_tier[r["model"]].append(r)

    print(f"{'tier':>8} {'n':>3} {'resolved':>9} {'mean cost':>10} {'total cost':>11} "
          f"{'mean in-tok':>12} {'mean out-tok':>12} {'mean turns':>10} {'mean wall':>10}")
    totals: dict[str, float] = {}
    for tier in ("haiku", "sonnet", "opus"):
        rs = by_tier[tier]
        costs = [r["cost_usd"] for r in rs]
        totals[tier] = sum(costs)
        print(
            f"{tier:>8} {len(rs):>3} {sum(r['resolved'] for r in rs):>9} "
            f"{statistics.mean(costs):>10.4f} {sum(costs):>11.4f} "
            f"{statistics.mean(r['input_tokens'] for r in rs):>12.0f} "
            f"{statistics.mean(r['output_tokens'] for r in rs):>12.0f} "
            f"{statistics.mean(r['turns'] for r in rs):>10.1f} "
            f"{statistics.mean(r['wall_clock_s'] for r in rs):>10.1f}"
        )
    if totals["haiku"]:
        print(f"\ncheap tier cost share: haiku {totals['haiku']/sum(totals.values()):.1%} of total")


if __name__ == "__main__":
    main()
