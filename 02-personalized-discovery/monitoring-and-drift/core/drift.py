"""Monitoring and drift, read: the prediction stayed flat; the world
did not.

Stage 47 introduces online monitoring. Offline evaluation reuses the
same snapshot the model was trained on, so it cannot see a serving-time
break. The online signal that can is the gap between what the model
predicted and what users actually did, tracked per hour.

Run:
    uv run python core/drift.py
    uv run python core/drift.py --emit-log /tmp/drift-envelope.json

The `--emit-log` flag writes the hourly trace plus the per-slice
observed series so the production path in `prod/slice_drift.py` can run
the slice-aware drift panel the way a monitoring team drills into a
flat aggregate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Hourly rows: predicted CTR stays 0.040; observed CTR falls as a price
# feature silently breaks at hour 5 and returns values of zero.
OBSERVED = [0.039, 0.041, 0.038, 0.040, 0.036, 0.031, 0.028, 0.026, 0.023, 0.021, 0.022, 0.020]

# The same class of break, confined to a small slice: category-a items
# carry the price feature that breaks, and the aggregate barely moves.
SLICES = {
    "homepage": {"share": 0.90, "observed": [0.040, 0.041, 0.039, 0.040, 0.041, 0.040, 0.039, 0.040, 0.041, 0.040, 0.040, 0.039]},
    "category-a": {"share": 0.06, "observed": [0.041, 0.040, 0.039, 0.040, 0.038, 0.033, 0.028, 0.024, 0.019, 0.015, 0.012, 0.010]},
    "new-users": {"share": 0.04, "observed": [0.040, 0.039, 0.041, 0.040, 0.039, 0.037, 0.036, 0.035, 0.034, 0.034, 0.033, 0.033]},
}


def aggregate_observed() -> list[float]:
    """The diluted aggregate: what the page-level panel would see."""
    return [
        round(
            sum(SLICES[s]["share"] * SLICES[s]["observed"][hour] for s in SLICES),
            3,
        )
        for hour in range(len(OBSERVED))
    ]


def render() -> None:
    print("monitoring and drift, read (12 hours, predicted ctr 0.040):")
    gap_ewma = 0.0
    alert_streak = 0
    for hour, observed in enumerate(OBSERVED):
        gap = 0.040 - observed
        gap_ewma = 0.7 * gap_ewma + 0.3 * gap
        if gap_ewma > 0.010:
            alert_streak += 1
            flag = " ALERT" if alert_streak >= 3 else ""
        else:
            alert_streak = 0
            flag = ""
        print(f"  hour {hour:>2}: predicted 0.040, observed {observed:.3f}, "
              f"gap {gap:.3f}, ewma {gap_ewma:.3f}{flag}")
    diluted = aggregate_observed()
    print("\nslice view (same break, confined to a 6% slice):")
    for name in SLICES:
        final = SLICES[name]["observed"][-1]
        print(f"  {name:<11} share {SLICES[name]['share']:.0%}, "
              f"observed {SLICES[name]['observed'][0]:.3f} to {final:.3f}")
    print(f"  {'aggregate':<11} diluted {diluted[0]:.3f} to {diluted[-1]:.3f}")
    print("\nreading: the model kept predicting 0.040 while users")
    print("clicked less every hour. The offline eval cannot see this -")
    print("its labels come from the same broken world. The prediction-")
    print("observation gap, tracked online, is what catches the")
    print("regression nobody flagged. Confined to a small slice, the")
    print("same break is invisible in the diluted aggregate.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the trace and slices as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        envelope = {
            "predicted": 0.040,
            "threshold": 0.010,
            "hours": len(OBSERVED),
            "observed": OBSERVED,
            "diluted": aggregate_observed(),
            "slices": SLICES,
        }
        Path(args.emit_log).write_text(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    sys.exit(main())
