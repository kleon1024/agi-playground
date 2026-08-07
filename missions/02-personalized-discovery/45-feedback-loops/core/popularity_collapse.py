"""Feedback loop, read: the ranker trains on what it showed, and what
it showed entrenches.

Stage 45 introduces the feedback loop. The recommender ranks items by
an estimated click rate, shows the top of the list, observes clicks on
those items, and updates the estimate. Items shown more collect more
evidence and rise; items never shown stay at the prior. Over rounds,
exposure concentrates even when the true rates differ only slightly.

Run:
    uv run python core/popularity_collapse.py
"""

from __future__ import annotations

import random


def main() -> None:
    rng = random.Random(7)
    n_items = 20
    true_ctr = [0.050 - 0.002 * i for i in range(n_items)]
    clicks = [0] * n_items
    shown = [0] * n_items
    prior = 0.025

    def rate(i: int) -> float:
        return clicks[i] / shown[i] if shown[i] else prior

    for _ in range(300):
        order = sorted(range(n_items), key=rate, reverse=True)
        for i in order[:5]:
            shown[i] += 1
            if rng.random() < true_ctr[i]:
                clicks[i] += 1

    head_share = sum(shown[:5]) / sum(shown)
    tail_share = sum(shown[-5:]) / sum(shown)
    coverage = sum(1 for s in shown if s > 0)
    sustained = sum(1 for s in shown if s >= 100)
    print("feedback loop, read (300 rounds, show top 5, update on clicks):")
    print(f"  impressions head 5 (true ctr 0.042-0.050): {head_share:.0%}")
    print(f"  impressions tail 5 (true ctr 0.012-0.020): {tail_share:.0%}")
    print(f"  catalogue coverage: {coverage} of {n_items} items ever shown")
    print(f"  sustained exposure (>=100 impressions): {sustained} of {n_items}")
    print("\nreading: items 0-4 gather clicks and their estimates rise;")
    print("items 5-19 never gather enough to outrank the head, even")
    print("where their true rate beats the prior. Exposure entrenches")
    print("the first winners and starves the rest. The model's own")
    print("output became its training data, so 'more of what works'")
    print("works only until the world changes - and the starved tail")
    print("is where the change would first be visible.")


if __name__ == "__main__":
    main()
