"""Privacy budget split, read: noise grows with every query answered.

Stage 40 adds DP noise per report. This script reads how splitting a
fixed privacy budget across many queries raises per-query noise.

Run:
    uv run python core/budget_split.py
"""

from __future__ import annotations


def main() -> None:
    total_epsilon = 2.0
    print("privacy budget split, read (total epsilon 2.0):")
    for queries in (1, 10, 100):
        per_query = total_epsilon / queries
        noise = 1.0 / per_query
        print(f"  {queries:>3} queries: epsilon {per_query:.3f} each, noise scale {noise:.1f}")
    print("\nreading: one report gets epsilon 2.0 and noise scale 0.5;")
    print("100 reports get epsilon 0.02 each and noise scale 50. The")
    print("privacy budget is a shared resource — every additional report")
    print("dilutes the signal of all the others.")


if __name__ == "__main__":
    main()
