"""When the negative rate is extreme: at 1:100,000, easy negatives
flood the gradient and a few positives are all the signal the model
sees. Downsampling plus correction is not optional here.

Run:
    uv run python core/extreme_negative.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def grad_mass(xs: list[list[float]], ys: list[int]) -> tuple[float, float]:
    """Gradient-norm share contributed by positives vs negatives."""
    gpos = 0.0
    gneg = 0.0
    for x, y in zip(xs, ys):
        p = sigmoid(sum(x) * 0.1)
        g = abs(p - y)
        if y == 1:
            gpos += g
        else:
            gneg += g
    tot = gpos + gneg
    return gpos / tot, gneg / tot


def main() -> None:
    rng = random.Random(31)
    pos = [[rng.gauss(1.0, 0.5) for _ in range(8)] for _ in range(100)]
    neg = [[rng.gauss(-1.0, 0.5) for _ in range(8)] for _ in range(100000)]
    gp, gn = grad_mass(pos + neg[:10000], [1] * 100 + [0] * 10000)
    print("when the negative rate is extreme, read (gradient flood):")
    print(f"  positives   100  of 100,100  gradient share {gp:.1%}")
    print(f"  negatives 10,000 of 100,100  gradient share {gn:.1%}")
    print()
    print("reading: at 1:1000 the easy negatives dominate the gradient even")
    print("when the model is still wrong, so the few positives barely move")
    print("the weights. downsampling negatives and correcting the rate is")
    print("what gives the positive signal a vote at all.")


if __name__ == "__main__":
    main()
