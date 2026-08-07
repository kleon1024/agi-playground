"""Interleaving, read: two rankings judged in one list per query.

Stage 38 is the frontier of online evaluation: instead of assigning
users to one ranking, interleaving shows a blend and credits each click
to the team that proposed the clicked result. This script reads one
interleaved list and its team credit.

Run:
    uv run python core/interleave_read.py
"""

from __future__ import annotations


def main() -> None:
    team_a = ["d1", "d2", "d3"]
    team_b = ["d4", "d2", "d5"]
    interleaved = ["d1", "d4", "d2", "d3", "d5"]
    clicks = ["d4", "d2"]
    credit_a = sum(1 for d in clicks if d in team_a)
    credit_b = sum(1 for d in clicks if d in team_b)
    print("interleaving, read:")
    print(f"  team_a: {team_a}")
    print(f"  team_b: {team_b}")
    print(f"  interleaved: {interleaved}")
    print(f"  clicks: {clicks}")
    print(f"  credit: team_a {credit_a}, team_b {credit_b}")
    print("\nreading: both users see one blended list, and clicks credit")
    print("the team that proposed each clicked result. Team b wins here")
    print("because d4 is its exclusive proposal. Interleaving needs far")
    print("fewer users than a between-user A/B, which is why online teams")
    print("use it for ranking changes.")


if __name__ == "__main__":
    main()
