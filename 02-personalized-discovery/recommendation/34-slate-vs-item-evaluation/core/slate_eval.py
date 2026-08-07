"""Slate evaluation, read: the best items are not the best page.

Stage 34 is the frontier of evaluation: item-level metrics rank items,
but the unit shown to a user is a slate. This script reads two slates
where the higher item-score sum loses on a slate-level metric.

Run:
    uv run python core/slate_eval.py
    uv run python core/slate_eval.py --emit-log /tmp/slate-metric-envelope.json

The `--emit-log` flag writes the audit cohort: 20 slate comparisons —
10 head and 10 tail — each with two slates scored two ways. Head
comparisons have a clear winner under both metrics; tail comparisons
are near ties, where the item-score sum and the diversity-adjusted
slate value pick different winners. The production path in
`prod/slate_metric_audit.py` measures the agreement rate per stratum,
the case-finding that shows which winner the item-level metric gets
wrong.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Audit cohort: slate comparisons, each with two slates scored two
# ways. Head comparisons have a clear winner under both metrics, so the
# item-level and slate-level metrics agree; tail comparisons are near
# ties, so the higher item-score sum loses on slate value once
# diversity counts — the two metrics pick different winners.
AUDIT_SLATES = {
    "head": [
        {"a": [["a1", 0.95, 1], ["a2", 0.90, 2], ["a3", 0.88, 3]],
         "b": [["b1", 0.80, 1], ["b2", 0.78, 1], ["b3", 0.75, 2]]},
        {"a": [["a1", 0.92, 1], ["a2", 0.91, 2], ["a3", 0.85, 3]],
         "b": [["b1", 0.82, 1], ["b2", 0.80, 2], ["b3", 0.78, 1]]},
        {"a": [["a1", 0.90, 1], ["a2", 0.89, 2], ["a3", 0.87, 3]],
         "b": [["b1", 0.84, 1], ["b2", 0.83, 2], ["b3", 0.81, 3]]},
        {"a": [["a1", 0.93, 1], ["a2", 0.88, 2], ["a3", 0.86, 3]],
         "b": [["b1", 0.79, 1], ["b2", 0.77, 2], ["b3", 0.76, 2]]},
        {"a": [["a1", 0.94, 1], ["a2", 0.89, 2], ["a3", 0.84, 3]],
         "b": [["b1", 0.83, 1], ["b2", 0.82, 2], ["b3", 0.80, 3]]},
        {"a": [["a1", 0.96, 1], ["a2", 0.90, 2], ["a3", 0.82, 3]],
         "b": [["b1", 0.85, 1], ["b2", 0.83, 2], ["b3", 0.80, 2]]},
        {"a": [["a1", 0.91, 1], ["a2", 0.90, 2], ["a3", 0.89, 3]],
         "b": [["b1", 0.86, 1], ["b2", 0.84, 2], ["b3", 0.82, 3]]},
        {"a": [["a1", 0.89, 1], ["a2", 0.87, 2], ["a3", 0.85, 3]],
         "b": [["b1", 0.78, 1], ["b2", 0.76, 2], ["b3", 0.75, 2]]},
        {"a": [["a1", 0.92, 1], ["a2", 0.90, 2], ["a3", 0.88, 3]],
         "b": [["b1", 0.81, 1], ["b2", 0.80, 2], ["b3", 0.79, 2]]},
        {"a": [["a1", 0.95, 1], ["a2", 0.88, 2], ["a3", 0.83, 3]],
         "b": [["b1", 0.82, 1], ["b2", 0.80, 2], ["b3", 0.79, 3]]},
    ],
    "tail": [
        {"a": [["a1", 0.85, 1], ["a2", 0.84, 1], ["a3", 0.83, 1]],
         "b": [["b1", 0.80, 2], ["b2", 0.79, 3], ["b3", 0.78, 4]]},
        {"a": [["a1", 0.84, 1], ["a2", 0.83, 1], ["a3", 0.82, 1]],
         "b": [["b1", 0.79, 2], ["b2", 0.78, 3], ["b3", 0.77, 4]]},
        {"a": [["a1", 0.86, 1], ["a2", 0.85, 1], ["a3", 0.84, 1]],
         "b": [["b1", 0.81, 2], ["b2", 0.80, 3], ["b3", 0.79, 4]]},
        {"a": [["a1", 0.83, 1], ["a2", 0.82, 1], ["a3", 0.81, 1]],
         "b": [["b1", 0.78, 2], ["b2", 0.77, 3], ["b3", 0.76, 4]]},
        {"a": [["a1", 0.87, 1], ["a2", 0.86, 1], ["a3", 0.85, 1]],
         "b": [["b1", 0.82, 2], ["b2", 0.81, 3], ["b3", 0.80, 4]]},
        {"a": [["a1", 0.85, 1], ["a2", 0.84, 1], ["a3", 0.82, 1]],
         "b": [["b1", 0.80, 2], ["b2", 0.79, 3], ["b3", 0.78, 4]]},
        {"a": [["a1", 0.84, 1], ["a2", 0.83, 1], ["a3", 0.82, 1]],
         "b": [["b1", 0.79, 2], ["b2", 0.78, 3], ["b3", 0.76, 4]]},
        {"a": [["a1", 0.86, 1], ["a2", 0.85, 1], ["a3", 0.83, 1]],
         "b": [["b1", 0.81, 2], ["b2", 0.80, 3], ["b3", 0.79, 4]]},
        {"a": [["a1", 0.85, 1], ["a2", 0.84, 1], ["a3", 0.83, 1]],
         "b": [["b1", 0.80, 2], ["b2", 0.78, 3], ["b3", 0.77, 4]]},
        {"a": [["a1", 0.87, 1], ["a2", 0.86, 1], ["a3", 0.84, 1]],
         "b": [["b1", 0.82, 2], ["b2", 0.81, 3], ["b3", 0.80, 4]]},
    ],
}


def item_sum(slate: list[list]) -> float:
    return sum(float(s) for _, s, _ in slate)


def slate_value(slate: list[list]) -> float:
    # relevance sum with a small diversity multiplier per distinct cover
    distinct = len({d for _, _, d in slate})
    return item_sum(slate) * (1.0 + 0.2 * distinct)


def render() -> None:
    # (item, relevance, diversity contribution)
    slate_a = [("a1", 0.9, 1), ("a2", 0.85, 1), ("a3", 0.8, 1)]
    slate_b = [("b1", 0.7, 3), ("b2", 0.7, 4), ("b3", 0.7, 5)]
    print("slate evaluation, read:")
    print(
        f"  slate_a item-score sum: {item_sum(slate_a):.2f}, "
        f"slate value {slate_value(slate_a):.2f}"
    )
    print(
        f"  slate_b item-score sum: {item_sum(slate_b):.2f}, "
        f"slate value {slate_value(slate_b):.2f}"
    )
    print("\nreading: slate_a wins on item scores (2.55 vs 2.10) but loses")
    print("on slate value (3.06 vs 3.36) once diversity counts. Item-level")
    print("metrics rank items; the user experiences the slate, which is")
    print("why stage 06's mixing and this frontier evaluation agree.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the audit cohort as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        Path(args.emit_log).write_text(json.dumps({"slates": AUDIT_SLATES}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
