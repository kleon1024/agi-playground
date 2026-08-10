"""Filter bubble closes, read: the user's own history narrows what
they are ever offered.

Stage 45 detour: per-user personalization feeds the user's clicks
back into the ranking. Over epochs, exposure concentrates on the
categories the user clicked once, and the rest of the catalogue
becomes unreachable - a bubble the user did not choose.

Run:
    uv run python core/filter_bubble.py
"""

from __future__ import annotations

N_CATEGORIES = 6
TRUE_TASTE = {2, 3}  # the user's true preferences
CATEGORY_CTR = [0.040, 0.034, 0.028, 0.022, 0.016, 0.010]


def main() -> None:
    affinity = [1.0] * N_CATEGORIES
    checkpoints = {1, 5, 10}
    print("filter bubble, read (per-user exposure by epoch):")
    for epoch in range(1, 11):
        if epoch in checkpoints:
            liked_share = sum(
                a for c, a in enumerate(affinity) if c in TRUE_TASTE
            ) / sum(affinity)
            print(f"  epoch {epoch}: liked-category share {liked_share:.0%}")
        for c in range(N_CATEGORIES):
            affinity[c] *= 1.25 if c in TRUE_TASTE else 0.85
    print("\nreading: each epoch the user clicks the liked categories")
    print("and the ranking amplifies them; the rest decay. Liked")
    print("exposure climbs from a third to most of the page by epoch")
    print("10 - the bubble closes from the inside, and the user never")
    print("chose it. The feedback loop is not just a popularity story;")
    print("it is a per-user one, and the same multiplicative dynamics")
    print("that concentrate the head concentrate a user's view.")


if __name__ == "__main__":
    main()
