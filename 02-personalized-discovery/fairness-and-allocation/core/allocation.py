"""Fairness and allocation, read: exposure is a budget the ranker
allocates.

Stage 53 introduces allocation. A click-optimal ranker gives most
exposure to the categories that click best. A fairness constraint
reserves a minimum share for the rest. The constraint costs some
aggregate CTR; the question is what the exposure buys.

Run:
    uv run python core/allocation.py
    uv run python core/allocation.py --emit-log /tmp/allocation-envelope.json

The `--emit-log` flag writes the per-floor-level exposure rows so the
production path in `prod/allocation_audit.py` can answer the
case-finding question of the stage: a declared fairness floor is not
the same as the exposure the protected group actually receives, and the
gap is invisible until you measure per-group exposure per floor level.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CATEGORIES = [
    {"name": "audio", "ctr": 0.040},
    {"name": "video", "ctr": 0.032},
    {"name": "cable", "ctr": 0.022},
    {"name": "accessories", "ctr": 0.010},
]

# The protected group this allocation is meant to reach: the long-tail
# category. The audit tracks its actual exposure share per floor level.
PROTECTED = "accessories"


def exposure_share(ctrs: list[float]) -> list[float]:
    """Exposure under top-k click ranking: winner-take-most."""
    weights = [c ** 3 for c in ctrs]
    total = sum(weights)
    return [w / total for w in weights]


def constrained_share(ctrs: list[float], floor: float) -> list[float]:
    """Give each category at least `floor`, renormalised."""
    shares = exposure_share(ctrs)
    for i in range(len(shares)):
        shares[i] = max(shares[i], floor)
    total = sum(shares)
    return [s / total for s in shares]


def sweep(floors: list[float]) -> list[dict[str, float]]:
    """Per-floor-level rows: each category's exposure and aggregate CTR."""
    ctrs = [c["ctr"] for c in CATEGORIES]
    rows = []
    for floor in floors:
        shares = constrained_share(ctrs, floor)
        row: dict[str, float] = {"floor": floor}
        for cat, share in zip(CATEGORIES, shares):
            row[cat["name"]] = share
        row["aggregate_ctr"] = sum(s * c for s, c in zip(shares, ctrs))
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the floor-level rows as JSON")
    args = parser.parse_args()
    ctrs = [c["ctr"] for c in CATEGORIES]
    print("fairness and allocation, read (exposure by category):")
    plain = exposure_share(ctrs)
    floored = constrained_share(ctrs, 0.10)
    plain_ctr = sum(s * c for s, c in zip(plain, ctrs))
    floor_ctr = sum(s * c for s, c in zip(floored, ctrs))
    print("  unconstrained:")
    for cat, share in zip(CATEGORIES, plain):
        print(f"    {cat['name']:<12} ctr {cat['ctr']:.3f} exposure {share:.0%}")
    print(f"    aggregate ctr: {plain_ctr:.4f}")
    print("  with a 10% per-category floor:")
    for cat, share in zip(CATEGORIES, floored):
        print(f"    {cat['name']:<12} ctr {cat['ctr']:.3f} exposure {share:.0%}")
    print(f"    aggregate ctr: {floor_ctr:.4f}")
    print("\nreading: the floor moves accessories from near-invisible to")
    print("a real share and costs a little aggregate ctr. Allocation is")
    print("a constraint on the ranking objective, and the price of the")
    print("constraint is measured, not assumed.")
    floors = [0.00, 0.05, 0.10, 0.15, 0.20]
    print("\nfloor sweep (protected-group exposure per floor level):")
    print(f"  {'floor':>6} {'accessories':>12} {'aggregate ctr':>14}")
    for row in sweep(floors):
        print(f"  {row['floor']:>6.0%} {row[PROTECTED]:>12.1%} "
              f"{row['aggregate_ctr']:>14.4f}")
    print("\n  reading: the declared floor never quite lands on the")
    print("  protected group - at a 10% floor, accessories receive 9.2%")
    print("  of exposure because renormalising after the floor re-")
    print("  dilutes it. Measure per-group exposure, not the declared")
    print("  floor, before declaring the allocation fair.")
    if args.emit_log:
        Path(args.emit_log).write_text(
            json.dumps({
                "floors": sweep(floors),
                "categories": CATEGORIES,
                "protected": PROTECTED,
            })
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
