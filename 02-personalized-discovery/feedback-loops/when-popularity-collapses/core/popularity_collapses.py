"""Popularity collapses, read: when the world changes, the loop is
the last to notice.

Stage 45 detour: at round 150 the true CTR of a starved tail item
jumps above the head. The loop keeps serving the entrenched head
because the tail never gets the impressions its new rate would earn.
The change is invisible until the head itself decays.

Run:
    uv run python core/popularity_collapses.py
"""

from __future__ import annotations

import random


def main() -> None:
    rng = random.Random(9)
    n_items = 20
    true_ctr = [0.050 - 0.002 * i for i in range(n_items)]
    clicks = [0] * n_items
    shown = [0] * n_items
    prior = 0.025

    def rate(i: int) -> float:
        return clicks[i] / shown[i] if shown[i] else prior

    head_share_at_end = 0.0
    for round_no in range(300):
        if round_no == 150:
            true_ctr[15] = 0.060  # a starved item suddenly becomes best
        order = sorted(range(n_items), key=rate, reverse=True)
        for i in order[:5]:
            shown[i] += 1
            if rng.random() < true_ctr[i]:
                clicks[i] += 1
        if round_no == 299:
            head_share_at_end = sum(shown[:5]) / sum(shown)

    winner_share = shown[15] / sum(shown)
    print("popularity collapses, read (item 15's true ctr jumps at round 150):")
    print(f"  item 15 impressions share: {winner_share:.1%}")
    print(f"  head 5 impressions share at round 300: {head_share_at_end:.0%}")
    print("\nreading: item 15 became the best item at round 150, and by")
    print("round 300 it holds a sliver of exposure. The loop cannot")
    print("discover a winner it never shows; 'more of what works'")
    print("works until the world changes, and the collapse is the")
    print("cost of entrenchment. Exploration is the repair, and it")
    print("must be budgeted before the change, not after.")


if __name__ == "__main__":
    main()
