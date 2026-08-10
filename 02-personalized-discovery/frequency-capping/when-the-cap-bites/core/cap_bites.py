"""When the cap bites, read: the floor cuts into reach.

Stage 25 caps exposure per user. This script reads the reach cost: a cap
that protects value also limits how many users a campaign can reach.

Run:
    uv run python core/cap_bites.py
"""

from __future__ import annotations


def main() -> None:
    budget = 10_000  # impressions to spend
    print("cap bites, read (10,000-impression budget):")
    for cap in (1, 3, 5, 10):
        users = budget // cap
        print(f"  cap {cap}: reaches {users:,} users at {cap} impressions each")
    print("\nreading: the same budget reaches 10,000 users at cap 1 and only")
    print("1,000 at cap 10. A high cap preserves per-user value but shrinks")
    print("reach; the campaign's goal decides which side of the trade it")
    print("needs. The cap is a budget allocation, not a display setting.")


if __name__ == "__main__":
    main()
