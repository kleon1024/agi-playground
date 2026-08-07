"""CAC exceeds LTV, read: the user who costs more than they return is
a liability at any volume.

Stage 55 detour: acquisition channels differ in cost and in the
retention of the users they bring. A channel whose users leave fast
is expensive no matter how cheap the install - every signup loses
money, and scaling the channel scales the loss.

Run:
    uv run python core/cac_exceeds_ltv.py
"""

from __future__ import annotations

CHANNELS = [
    {"name": "organic search", "cac": 2.0, "retention": [1.00, 0.45, 0.38, 0.32, 0.28]},
    {"name": "referral", "cac": 3.5, "retention": [1.00, 0.40, 0.30, 0.24, 0.20]},
    {"name": "paid installs", "cac": 8.0, "retention": [1.00, 0.28, 0.13, 0.06, 0.03]},
]

REVENUE_PER_MONTH = 5.0


def main() -> None:
    print("cac exceeds ltv, read (revenue $5/user/month, 5 months):")
    for channel in CHANNELS:
        ltv = sum(r * REVENUE_PER_MONTH for r in channel["retention"])
        ratio = ltv / channel["cac"]
        verdict = "profitable" if ratio >= 1.0 else "loses money"
        print(f"  {channel['name']:<15} cac ${channel['cac']:.2f}, "
              f"ltv ${ltv:.2f}, ltv/cac {ratio:.2f} ({verdict})")
    print("\nreading: referral clears its cost; paid installs do not.")
    print("The decision is not the install price - it is the months")
    print("after it. A channel with LTV below CAC pays the platform to")
    print("grow, and volume makes the loss larger.")


if __name__ == "__main__":
    main()
