"""Preference optimization, read: the ranker trained on pairwise choices.

Stage 32 is RLHF applied to ranking: instead of predicting a score,
the model learns from pairwise preferences which item the user chose.
This script reads a Bradley-Terry log loss step on three preference
pairs.

Run:
    uv run python core/preference_opt.py
"""

from __future__ import annotations

import math


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def main() -> None:
    # (chosen score, rejected score) pairs with the model's logits.
    pairs = [(1.2, 0.4), (0.9, 0.8), (0.3, 1.1)]
    print("preference optimization, read (Bradley-Terry log loss):")
    total = 0.0
    for chosen, rejected in pairs:
        logit = chosen - rejected
        p = sigmoid(logit)
        loss = -math.log(p)
        total += loss
        print(
            f"  chosen {chosen} vs rejected {rejected}: "
            f"logit {logit:.1f}, p {p:.2f}, loss {loss:.2f}"
        )
    print(f"  total loss: {total:.2f}")
    print("\nreading: the model is pushed to widen the gap between the")
    print("chosen and the rejected item. The loss is the negative log")
    print("probability of the preference; real RLHF optimizes it over")
    print("sampled pairs, which is where the reward-hacking detour lives.")


if __name__ == "__main__":
    main()
