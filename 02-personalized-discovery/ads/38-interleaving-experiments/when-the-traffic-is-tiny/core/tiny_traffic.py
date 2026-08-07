"""Tiny traffic, read: the power of interleaving on a small launch.

Stage 38 uses interleaving for online evaluation. This script reads
why interleaving still reaches significance where a between-user A/B
would not.

Run:
    uv run python core/tiny_traffic.py
"""

from __future__ import annotations


def main() -> None:
    # (design, users needed, users available)
    designs = [
        ("between-user A/B", 10_000, 800),
        ("interleaving", 400, 800),
    ]
    print("tiny traffic, read (800 users available):")
    for name, needed, available in designs:
        feasible = needed <= available
        print(f"  {name}: needs {needed:,}, available {available:,}, feasible {feasible}")
    print("\nreading: with 800 users the A/B never reaches significance,")
    print("while interleaving needs 400 and ships. For a ranking change")
    print("the unit of comparison is the list, not the user — which is")
    print("why interleaving is the standard online tool for ranking teams")
    print("with limited traffic.")


if __name__ == "__main__":
    main()
