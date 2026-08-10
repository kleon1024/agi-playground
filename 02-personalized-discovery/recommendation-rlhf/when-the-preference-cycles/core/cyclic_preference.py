"""Cyclic preferences, read: the preference the scalar model cannot hold.

Stage 32 optimizes a ranker from pairwise preferences under a
Bradley-Terry scalar reward: every item gets one score, and the score
ranks them. A scalar order is transitive by construction — if A beats B
and B beats C, the model must rank A above C. But human and user
preferences are not always transitive: A over B, B over C, and C over
A is a cycle that no single score can represent.

This script reads what an Elo-style scalar model does when fitted to a
three-item cycle.

Run:
    uv run python core/cyclic_preference.py
"""

from __future__ import annotations

import math


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def main() -> None:
    # The observed cycle: A beats B, B beats C, C beats A.
    games = [("A", "B"), ("B", "C"), ("C", "A")]
    rating = {"A": 0.0, "B": 0.0, "C": 0.0}
    k = 1.0
    last_swing = 0.0
    for _ in range(1000):
        max_step = 0.0
        for winner, loser in games:
            expected = sigmoid(rating[winner] - rating[loser])
            step = k * (1.0 - expected)
            rating[winner] += step
            rating[loser] -= step
            max_step = max(max_step, step)
        last_swing = max_step

    print("cyclic preference, read (A > B, B > C, C > A):")
    print(f"  fitted scalar ratings: A {rating['A']:.2f}, "
          f"B {rating['B']:.2f}, C {rating['C']:.2f}")
    print(f"  last-update swing after 1000 iterations: {last_swing:.3f}")
    print()
    print("  pairwise predictions:")
    contradictions = 0
    for winner, loser in games:
        predicted = "matches" if rating[winner] > rating[loser] else "CONTRADICTS"
        if predicted == "CONTRADICTS":
            contradictions += 1
        print(f"    {winner} vs {loser}: predicted {winner} wins "
              f"({sigmoid(rating[winner] - rating[loser]):.2f}) -- {predicted}")
    print()
    print(f"  contradictions: {contradictions} of 3 edges")
    print("\nreading: a scalar model is transitive by construction, and a")
    print("cycle has no consistent scalar answer — the ratings keep")
    print(f"rotating -- the last-update swing ({last_swing:.3f}) does not")
    print("decay toward zero, so no fitted score ever settles -- and at")
    print("least one observed edge is always predicted wrong. The")
    print("pipeline has to detect the cycle (count cyclic triples among")
    print("sampled pairs) and either drop the weakest edge or model the")
    print("preference as context-dependent instead of a single score")
    print("(Zhang et al. 2025).")


if __name__ == "__main__":
    main()
