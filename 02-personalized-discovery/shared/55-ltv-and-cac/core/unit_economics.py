"""LTV and CAC, read: a user is worth what they keep returning and
spending; acquiring them costs what it costs.

Stage 55 introduces unit economics. Lifetime value is retention times
revenue per retained user; acquisition cost is what a channel charges
for a signup. The ratio decides which channels the platform can afford
to buy users from at all.

Run:
    uv run python core/unit_economics.py
"""

from __future__ import annotations

CHANNELS = [
    {
        "name": "organic search",
        "cac": 2.0,
        "retention": [1.00, 0.45, 0.38, 0.32, 0.28],
        "revenue_per_month": 5.0,
    },
    {
        "name": "paid installs",
        "cac": 8.0,
        "retention": [1.00, 0.28, 0.13, 0.06, 0.03],
        "revenue_per_month": 5.0,
    },
]


def ltv(channel: dict[str, object]) -> float:
    retention = [float(r) for r in channel["retention"]]
    revenue = float(channel["revenue_per_month"])
    return sum(r * revenue for r in retention)


def main() -> None:
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


if __name__ == "__main__":
    main()
