"""The fusion weight, read: which matcher dominates the merged list.

Stage 21 fuses lexical and dense scores. This script shows a weighted
sum and reads how the winner changes with the weight.

Run:
    uv run python core/fusion_weight.py
"""

from __future__ import annotations


def main() -> None:
    # (doc, lexical score, dense score)
    docs = [("d1", 0.9, 0.4), ("d2", 0.3, 0.9), ("d3", 0.6, 0.6)]
    print("fusion weight, read (score = w*lex + (1-w)*dense):")
    for weight in (0.0, 0.5, 1.0):
        scores = [(d, weight * l + (1 - weight) * e) for d, l, e in docs]
        winner = max(scores, key=lambda x: x[1])
        print(f"  w={weight:.1f}: winner {winner[0]} ({winner[1]:.2f})")
    print("\nreading: at w=0 dense wins (d2, 0.90), at w=1 lexical wins")
    print("(d1, 0.90), and at w=0.5 d1 leads by 0.05. The weight is the")
    print("product decision: how much the platform trusts meaning versus")
    print("exact terms.")


if __name__ == "__main__":
    main()
