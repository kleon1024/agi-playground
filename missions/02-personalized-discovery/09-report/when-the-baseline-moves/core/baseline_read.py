"""The baseline that moved, read: beating popularity is time-indexed.

Stage 09 reports the mission outcome against a popularity baseline. This
script recomputes the baseline per period and shows the verdict changing
as the baseline drifts.

Run:
    uv run python core/baseline_read.py
"""

from __future__ import annotations


def main() -> None:
    # (period, personalized nDCG, popularity baseline nDCG)
    periods = [
        ("w1", 0.42, 0.38),
        ("w2", 0.45, 0.46),
        ("w3", 0.44, 0.39),
    ]
    print("the moving baseline, read:")
    for name, system, base in periods:
        verdict = "beats" if system > base else "LOSES"
        print(f"  {name}: system {system:.2f} vs baseline {base:.2f} -> {verdict}")
    print("\nreading: the same system beats popularity in week 1, loses in")
    print("week 2, and wins again in week 3 — the baseline is not a")
    print("constant, it is the demand curve. A report dated to one period")
    print("says when the win holds; it cannot promise forever.")


if __name__ == "__main__":
    main()
