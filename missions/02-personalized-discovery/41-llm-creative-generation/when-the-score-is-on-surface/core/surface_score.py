"""Surface score, read: the text features that miss real CTR.

Stage 41 scores generated creatives before delivery. This script reads
the gap between a surface score and measured CTR.

Run:
    uv run python core/surface_score.py
"""

from __future__ import annotations


def main() -> None:
    # (creative, surface score, measured CTR)
    rows = [
        ("'Buy now'", 0.9, 0.02),
        ("'Run faster, pay less'", 0.7, 0.08),
        ("'Marathon shoes, 20% off'", 0.6, 0.06),
    ]
    print("surface score, read:")
    for name, surface, ctr in rows:
        print(f"  {name}: surface {surface}, measured CTR {ctr:.2f}")
    best_surface = max(rows, key=lambda x: x[1])
    best_ctr = max(rows, key=lambda x: x[2])
    print(f"  surface winner: {best_surface[0]}")
    print(f"  CTR winner:     {best_ctr[0]}")
    print("\nreading: the surface score rewards urgency ('Buy now'), the")
    print("measured CTR rewards specificity. A launch that trusts the")
    print("surface score ships the wrong creative — the score has to be")
    print("calibrated against real delivery before it decides.")


if __name__ == "__main__":
    main()
