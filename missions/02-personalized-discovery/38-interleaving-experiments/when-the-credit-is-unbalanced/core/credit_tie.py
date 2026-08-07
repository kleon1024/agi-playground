"""Credit ties, read: the shared document both teams proposed.

Stage 38 credits clicks to the team that proposed the result. This
script reads the ambiguity when both rankings contain the clicked
document.

Run:
    uv run python core/credit_tie.py
"""

from __future__ import annotations


def main() -> None:
    team_a = ["d1", "d2", "d3"]
    team_b = ["d2", "d4", "d5"]
    clicks = ["d2"]
    in_a = clicks[0] in team_a
    in_b = clicks[0] in team_b
    print("credit tie, read:")
    print(f"  team_a: {team_a}")
    print(f"  team_b: {team_b}")
    print(f"  clicked: {clicks[0]} (in team_a {in_a}, in team_b {in_b})")
    print("\nreading: d2 appears in both rankings, so the click's credit")
    print("is ambiguous — both teams proposed it. Interleaving credit")
    print("needs a tie rule (first proposal, random split), or the shared")
    print("documents silently blur the comparison.")


if __name__ == "__main__":
    main()
