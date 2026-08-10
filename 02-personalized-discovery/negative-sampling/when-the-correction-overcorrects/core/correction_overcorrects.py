"""When the correction overcorrects: the inverse-sampling formula
assumes the sampling ratio is exact; a misestimated ratio leaves the
probabilities systematically off on one side or the other.

Run:
    uv run python core/correction_overcorrects.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def main() -> None:
    rng = random.Random(37)
    # true positive rate 0.5%: 200 positives, 39,800 negatives
    n = 40000
    ys = [1 if rng.random() < 0.005 else 0 for _ in range(n)]

    def ece(ps: list[float]) -> float:
        return sum(abs(p - y) for p, y in zip(ps, ys)) / n

    def correct(q: float, r_est: float) -> float:
        return q * r_est / (1.0 - q + q * r_est)

    q = 0.05  # a downsampled model that reports 5% (10x the true rate)
    rows = [(0.05, "exact ratio"), (0.03, "ratio too low"), (0.10, "ratio too high")]
    print("when the correction overcorrects, read (ratio misestimation):")
    print(f"  {'assumed ratio':<14}{'corrected p':>12}{'bias vs true':>14}")
    for r_est, note in rows:
        p_c = correct(q, r_est)
        print(f"  {note:<14}{p_c:>12.3f}{p_c - 0.005:>14.3f}")
    print()
    print("reading: the formula is only as good as the ratio it is fed. if")
    print("operations believes 1:10 and actually ran 1:20, the corrected")
    print("probabilities land half a decimal too high; calibrating against")
    print("the observed base rate after correction is the check that catches")
    print("a wrong ratio, and it is why sampling ratios are logged, not assumed.")


if __name__ == "__main__":
    main()
