"""Epsilon flip rate, audited: how often the noise moves the budget.

Stage 40's executed draw added noise at epsilon 2.0 and flipped the
display/email order once. This audit asks the industrial question that
single draw skips: how often does that happen? It sweeps epsilon and
measures, over 1,000 fixed-seed draws per level under the stage's own
noise model (uniform noise of range 100 / epsilon on each channel
count), the rate at which the noise flips the display/email pair that
decides the second budget allocation.

Run:
    uv run python core/epsilon_flip.py
"""

from __future__ import annotations

import random

TRUE_COUNTS = {"search": 480.0, "display": 310.0, "email": 260.0}
DRAWS = 1_000
PAIR = ("display", "email")


def flip_rate(epsilon: float, seed: int) -> tuple[float, float, float]:
    """Flip rates: the close pair, the top slot, and the full order."""
    rng = random.Random(seed)
    noise_range = 100.0 / epsilon
    pair_flips = 0
    top_flips = 0
    full_preserved = 0
    for _ in range(DRAWS):
        noisy = {
            k: v + rng.uniform(-noise_range, noise_range) for k, v in TRUE_COUNTS.items()
        }
        if noisy[PAIR[0]] < noisy[PAIR[1]]:
            pair_flips += 1
        if noisy["search"] < noisy["display"]:
            top_flips += 1
        true_order = sorted(TRUE_COUNTS, key=TRUE_COUNTS.get, reverse=True)
        if sorted(noisy, key=noisy.get, reverse=True) == true_order:
            full_preserved += 1
    return pair_flips / DRAWS, top_flips / DRAWS, full_preserved / DRAWS


def main() -> None:
    print("epsilon flip rate, audited: how often does the noise move budget?")
    print(f"  true counts: {', '.join(f'{k} {v:.0f}' for k, v in TRUE_COUNTS.items())}")
    print(f"  display-email gap: {TRUE_COUNTS['display'] - TRUE_COUNTS['email']:.0f}")
    print("  noise model: stage 40's uniform of range 100/epsilon per count")
    print(f"  {DRAWS} fixed-seed draws per epsilon level")
    print()

    print("epsilon | noise range | display/email flips | top-1 flips | "
          "full order kept")
    for epsilon in (5.0, 2.0, 1.0, 0.5, 0.25):
        pair, top, full = flip_rate(epsilon, 17)
        print(f"  {epsilon:5.2f} |      +/-{100.0 / epsilon:6.1f} | "
              f"{pair:6.1%}        | {top:6.1%}      | {full:6.1%}")
    print()

    pair_2 = flip_rate(2.0, 17)[0]
    weeks = 12
    any_flip = 1.0 - (1.0 - pair_2) ** weeks
    print("reading: the stage's own epsilon 2.0 sits exactly at the")
    print("boundary where the close pair can flip. The audit measures")
    print(f"the result: a {pair_2:.1%} display/email flip rate per report,")
    print(f"so a quarter of {weeks} weekly reports has a "
          f"{any_flip:.0%} chance of at least one")
    print("flipped allocation. At epsilon 5.0 the noise range is smaller")
    print("than the 50-count gap and the order never flips. The privacy")
    print("dial and the decision-accuracy dial are the same knob: epsilon")
    print("must clear the gap that matters (Dwork 2006; differentially")
    print("private ad-conversion measurement, PoPETs 2024).")


if __name__ == "__main__":
    main()
