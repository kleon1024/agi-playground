"""Retention flattens, read: the user who stops leaving is worth more
than the user who stops coming.

Stage 55 detour: two cohorts retain the same share in month one. One
keeps decaying; the other flattens at a floor. The flat cohort's LTV
keeps growing past the horizon, which is where the recommendation
system earns its keep - relevance is a retention lever.

Run:
    uv run python core/retention_flattens.py
"""

from __future__ import annotations

REVENUE_PER_MONTH = 5.0
MONTHS = 24


def retention(decay: float, floor: float) -> list[float]:
    out = [1.0]
    for _ in range(MONTHS - 1):
        out.append(max(floor, out[-1] * decay))
    return out


def main() -> None:
    decaying = retention(0.82, 0.0)
    flattening = retention(0.82, 0.35)
    print("retention flattens, read (24-month ltv per user):")
    print(f"  decaying cohort (floor 0):    ltv ${sum(r for r in decaying) * REVENUE_PER_MONTH:.2f}")
    print(f"  flattening cohort (floor 35%): ltv ${sum(r for r in flattening) * REVENUE_PER_MONTH:.2f}")
    print(f"  month 12 retention: decaying {decaying[-1]:.0%}, "
          f"flattening {flattening[-1]:.0%}")
    print("\nreading: both cohorts decay at the same rate for months;")
    print("the floor decides the difference. A 35% floor nearly doubles")
    print("LTV because the flat tail compounds over the horizon.")
    print("Retention work - which is what good discovery is - changes")
    print("the floor, and the floor is worth more than any single")
    print("month's revenue.")


if __name__ == "__main__":
    main()
