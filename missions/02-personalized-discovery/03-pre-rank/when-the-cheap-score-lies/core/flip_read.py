"""The cheap score that lies, read: pre-rank and fine-rank disagree.

Stage 03 cuts 1000 candidates to 100 with a cheap scorer. This script
counts how often the cheap score and the fine score order an item
differently, and what that does to the cut.

Run:
    uv run python core/flip_read.py
"""

from __future__ import annotations


def main() -> None:
    # 10 items with (cheap_score, fine_score), fine score is the truth.
    items = [
        (0.90, 0.31), (0.85, 0.62), (0.80, 0.18), (0.72, 0.55),
        (0.66, 0.44), (0.58, 0.70), (0.51, 0.33), (0.47, 0.60),
        (0.40, 0.28), (0.30, 0.52),
    ]
    by_cheap = sorted(range(len(items)), key=lambda i: items[i][0], reverse=True)
    by_fine = sorted(range(len(items)), key=lambda i: items[i][1], reverse=True)
    cheap_cut = set(by_cheap[:5])
    fine_cut = set(by_fine[:5])
    flips = len(cheap_cut.symmetric_difference(fine_cut))
    print("cheap score vs fine score, read (cut at 5 of 10):")
    for idx, (c, f) in enumerate(items):
        in_cheap = idx in cheap_cut
        in_fine = idx in fine_cut
        mark = "agree" if in_cheap == in_fine else "FLIP"
        print(f"  item {idx}: cheap {c:.2f} fine {f:.2f} "
              f"{'in' if in_cheap else 'out'}/{'in' if in_fine else 'out'} {mark}")
    print(f"\nreading: {flips} items sit on different sides of the cut.")
    print("The cheap cut is a filter, not a ranker — its errors")
    print("are the items it drops that the fine ranker would have kept.")


if __name__ == "__main__":
    main()
