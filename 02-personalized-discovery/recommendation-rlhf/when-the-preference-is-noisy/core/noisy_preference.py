"""Noisy preferences, read: the flipped pair the loss cannot fix.

Stage 32 optimizes a ranker from pairwise preferences. This script
reads what happens when some preference labels are flipped by noise.

Run:
    uv run python core/noisy_preference.py
"""

from __future__ import annotations


def main() -> None:
    # (chosen, rejected) true pairs; the third is flipped by label noise.
    pairs = [(1.2, 0.4), (0.9, 0.8), (0.3, 1.1)]
    total = 0.0
    print("noisy preference, read (1 of 3 labels flipped):")
    for chosen, rejected in pairs:
        if chosen < rejected:
            loss = abs(chosen - rejected)  # the flip forces a wrong gradient
            flag = " (flipped)"
        else:
            loss = max(0.0, 0.1 - (chosen - rejected) * 0.1)
            loss = 0.0 if chosen - rejected > 0.1 else loss
            flag = ""
        total += loss
        print(f"  chosen {chosen} vs rejected {rejected}: loss {loss:.2f}{flag}")
    print(f"  total loss floor: {total:.2f}")
    print("\nreading: the flipped pair pushes the model the wrong way and")
    print("sets a loss floor the clean pairs cannot remove. Real RLHF")
    print("labels are noisy, so the pipeline has to filter or reweight —")
    print("the frontier cost is label quality, not model capacity.")


if __name__ == "__main__":
    main()
