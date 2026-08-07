"""Privacy-safe attribution, read: noisy counts that still decide budget.

Stage 40 is the frontier of measurement: attribution counts get
differential-privacy noise so individual users cannot be tracked. This
script reads how noise changes the channel ranking that decides budget.

Run:
    uv run python core/dp_attribution.py
"""

from __future__ import annotations

import random


def main() -> None:
    random.seed(7)
    true = {"search": 480, "display": 310, "email": 260}
    epsilon = 2.0
    sensitivity = 1
    scale = sensitivity / epsilon
    noisy = {k: v + random.uniform(-scale, scale) * 100 for k, v in true.items()}
    true_rank = [k for k, _ in sorted(true.items(), key=lambda x: -x[1])]
    noisy_rank = [k for k, _ in sorted(noisy.items(), key=lambda x: -x[1])]
    print("privacy-safe attribution, read (epsilon 2.0):")
    for k, v in true.items():
        print(f"  {k}: true {v}, noisy {noisy[k]:.0f}")
    print(f"  true rank:  {true_rank}")
    print(f"  noisy rank: {noisy_rank}")
    print(f"  order preserved: {true_rank == noisy_rank}")
    print("\nreading: the noise hides any individual's contribution, but it")
    print("can reorder the channels that decide budget. Epsilon trades")
    print("privacy against decision accuracy — the noise-too-high detour")
    print("shows the collapse point.")


if __name__ == "__main__":
    main()
