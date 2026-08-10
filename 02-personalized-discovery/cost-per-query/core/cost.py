"""Cost per query, read: the cascade is arithmetic with a price tag.

Stage 50 introduces cost per query. Each funnel stage scores a smaller
set with a more expensive model. The cost of a query is the sum over
stages of candidates times per-candidate cost, and the cascade exists
because scoring ten million items with the fine model is unaffordable.

Run:
    uv run python core/cost.py
    uv run python core/cost.py --emit-log /tmp/cost-envelope.json

The `--emit-log` flag writes the per-stage costs at three catalogue
scales so the production path in `prod/cost_audit.py` can answer the
case-finding question of the stage: the dominant stage moves with the
catalogue, and the design that is flat at one size stops being flat at
the next.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# (stage, candidates scored, per-candidate cost units)
STAGES = [
    ("recall (ann)", 100_000, 0.00001),
    ("pre-rank", 1_000, 0.001),
    ("fine-rank", 50, 0.02),
    ("mixing", 20, 0.05),
]

EXHAUSTIVE = 10_000_000 * 0.02

# Recall candidates grow sublinearly with the catalogue: the ANN index
# serves more candidates as the catalogue grows, while the later stages
# keep fixed budgets. 100k candidates at 10M items, scaling as
# catalogue^0.4.
SCALES = [10_000_000, 100_000_000, 1_000_000_000]


def candidates_at(catalogue: int) -> dict[str, float]:
    recall = 100_000 * (catalogue / 10_000_000) ** 0.4
    return {
        "recall (ann)": recall,
        "pre-rank": 1_000,
        "fine-rank": 50,
        "mixing": 20,
    }


def scale_cost(catalogue: int) -> dict[str, object]:
    candidates = candidates_at(catalogue)
    per_stage = {
        name: candidates[name] * unit_cost
        for name, _, unit_cost in STAGES
    }
    total = sum(per_stage.values())
    return {
        "catalogue": catalogue,
        "per_stage": per_stage,
        "total": total,
    }


def render_scale(row: dict[str, object]) -> None:
    catalogue = row["catalogue"]
    per_stage = row["per_stage"]
    total = row["total"]
    label = f"{catalogue/1_000_000:.0f}M" if catalogue < 1_000_000_000 else "1B"
    print(f"  catalogue {label:>3}:")
    for name in ("recall (ann)", "pre-rank", "fine-rank", "mixing"):
        cost = per_stage[name]
        share = cost / total
        print(f"    {name:<10} {cost:>6.2f} units ({share:.0%})")
    print(f"    total {total:>6.2f} units")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the scale costs as JSON")
    args = parser.parse_args()
    print("cost per query, read (cost units):")
    total = 0.0
    for name, candidates, unit_cost in STAGES:
        cost = candidates * unit_cost
        total += cost
        print(f"  {name:<10} {candidates:>9,} candidates x {unit_cost:.5f} "
              f"= {cost:.1f}")
    print(f"  total per query: {total:.1f} units")
    print(f"  exhaustive fine-rank of 10M items: {EXHAUSTIVE:.0f} units")
    print(f"  per 1M queries, cascade: {total * 1_000_000:,.0f} units")
    print(f"  per 1M queries, exhaustive: {EXHAUSTIVE * 1_000_000:,.0f} units")
    print("\nreading: the cascade costs a fraction of exhaustive scoring,")
    print("and every stage exists to buy the next one a smaller problem.")
    print("Cost per query is the budget that capacity planning spends.")
    scale_rows = [scale_cost(s) for s in SCALES]
    print("\nscale view (the flat 1.0-each design at catalogue sizes):")
    for row in scale_rows:
        render_scale(row)
    if args.emit_log:
        Path(args.emit_log).write_text(
            json.dumps({"stages": [s[0] for s in STAGES], "scales": scale_rows})
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
