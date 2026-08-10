"""LTV and CAC, read: a user is worth what they keep returning and
spending; acquiring them costs what it costs.

Stage 55 introduces unit economics. Lifetime value is retention times
revenue per retained user; acquisition cost is what a channel charges
for a signup. The ratio decides which channels the platform can afford
to buy users from at all.

Run:
    uv run python core/unit_economics.py
    uv run python core/unit_economics.py --emit-log /tmp/unit-economics-envelope.json

The `--emit-log` flag writes each channel's full 24-month retention
curve so the production path in `prod/unit_economics_audit.py` can
answer the case-finding question of the stage: LTV/CAC is a curve over
the horizon, not a number, and the window you measure decides which
channel you call the acquisition bet.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CHANNELS = [
    {
        "name": "organic search",
        "cac": 2.0,
        "retention": [1.00, 0.45, 0.38, 0.32, 0.28],
        "tail": 0.85,
        "revenue_per_month": 5.0,
    },
    {
        "name": "paid installs",
        "cac": 8.0,
        "retention": [1.00, 0.28, 0.13, 0.06, 0.03],
        "tail": 0.60,
        "revenue_per_month": 5.0,
    },
    {
        "name": "referral",
        "cac": 4.0,
        "retention": [0.10, 0.20, 0.32, 0.40, 0.42],
        "tail": 0.98,
        "revenue_per_month": 5.0,
    },
]

HORIZONS = [1, 3, 6, 12, 24]


def ltv(channel: dict[str, object]) -> float:
    retention = [float(r) for r in channel["retention"]]
    revenue = float(channel["revenue_per_month"])
    return sum(r * revenue for r in retention)


def retention_curve(channel: dict[str, object], months: int = 24) -> list[float]:
    """The channel's full retention curve: declared seed months, then a
    geometric tail at the channel's decay factor."""
    seed = [float(r) for r in channel["retention"]]
    tail = float(channel["tail"])
    curve = list(seed)
    while len(curve) < months:
        curve.append(round(curve[-1] * tail, 3))
    return curve[:months]


def ltv_at(channel: dict[str, object], horizon: int) -> float:
    revenue = float(channel["revenue_per_month"])
    return sum(r * revenue for r in retention_curve(channel)[:horizon])


def render_horizons() -> None:
    print("\nhorizon view (ltv/cac per measured window):")
    print(f"  {'channel':<16} " + " ".join(f"{h:>4}m" for h in HORIZONS))
    for channel in CHANNELS:
        ratios = [ltv_at(channel, h) / float(channel["cac"]) for h in HORIZONS]
        print(f"  {channel['name']:<16} " + " ".join(f"{r:>6.2f}" for r in ratios))
    print("\n  reading: referral looks weak at 3 months (0.78) and")
    print("  dominant at 24 (10.0) because its users ramp slowly and")
    print("  stay; paid installs looks fine at 3 months (0.88) and")
    print("  never improves. The window you measure decides which")
    print("  channel you call the acquisition bet.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the retention curves as JSON")
    args = parser.parse_args()
    print("ltv and cac, read (5-month lifetime value per user):")
    for channel in CHANNELS:
        value = ltv(channel)
        cac = float(channel["cac"])
        ratio = value / cac if cac else 0.0
        print(f"  {channel['name']:<15} cac ${cac:.2f}, ltv ${value:.2f}, "
              f"ltv/cac {ratio:.2f}")
    print("\nreading: organic search pays back ~6x its acquisition cost;")
    print("paid installs return less than the cost of the user - every")
    print("paid signup loses money once retention is counted. A channel")
    print("with a low CAC is not a cheap channel if its users leave.")
    print("Unit economics decide which growth is real growth.")
    render_horizons()
    if args.emit_log:
        Path(args.emit_log).write_text(
            json.dumps({
                "horizons": HORIZONS,
                "channels": [
                    {
                        "name": c["name"],
                        "cac": float(c["cac"]),
                        "revenue_per_month": float(c["revenue_per_month"]),
                        "retention": retention_curve(c),
                    }
                    for c in CHANNELS
                ],
            })
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
