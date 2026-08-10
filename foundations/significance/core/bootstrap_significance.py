"""Quantify whether an observed pass-rate gap between two systems is real.

Two models are scored on the same held-out item set (paired design: item i's
difficulty affects both scores, so their per-item outcomes are correlated).
Model A carries a small, fixed true skill edge over Model B. Each item's pass
probability is item-difficulty plus per-model skill plus independent noise,
clamped to [0, 1]; the observed outcome is a single Bernoulli draw from that
probability, exactly like a real per-item pass/fail eval record.

The paired bootstrap (Efron, 1979; adopted for system comparison in Koehn,
2004, EMNLP) resamples item *indices* with replacement -- not A and B
independently -- so the same item difficulty cancels out of the differenced
statistic on every resample, same reason a paired t-test beats an unpaired one
here. Repeat the resample B times, recompute mean(A) - mean(B) each time, and
the spread of that resampled distribution is the confidence interval.

The same true_effect run at two item-set sizes shows the interval narrow
enough to exclude zero at n=300, and still include zero at n=25 -- the same
real effect, indistinguishable from noise purely as a function of how much
evidence was collected.

Usage:
    python bootstrap_significance.py --seed 0 --out ../runs/bootstrap-run.json
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

TRUE_EFFECT = 0.06
N_RESAMPLES = 2000
CI_LOW_PCT = 2.5
CI_HIGH_PCT = 97.5


def clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def generate_paired_outcomes(n_items: int, true_effect: float, seed: int) -> tuple:
    rng = random.Random(seed)
    outcomes_a = []
    outcomes_b = []
    for _ in range(n_items):
        difficulty = rng.uniform(0.3, 0.9)
        noise_a = rng.gauss(0.0, 0.15)
        noise_b = rng.gauss(0.0, 0.15)
        p_a = clamp(difficulty + true_effect / 2 + noise_a)
        p_b = clamp(difficulty - true_effect / 2 + noise_b)
        outcomes_a.append(1 if rng.random() < p_a else 0)
        outcomes_b.append(1 if rng.random() < p_b else 0)
    return outcomes_a, outcomes_b


def paired_bootstrap_ci(
    outcomes_a: list, outcomes_b: list, n_resamples: int, seed: int
) -> dict:
    n = len(outcomes_a)
    rng = random.Random(seed)
    observed_gap = sum(outcomes_a) / n - sum(outcomes_b) / n

    resampled_gaps = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        resampled_a = sum(outcomes_a[i] for i in idx) / n
        resampled_b = sum(outcomes_b[i] for i in idx) / n
        resampled_gaps.append(resampled_a - resampled_b)

    resampled_gaps.sort()
    low_rank = round(CI_LOW_PCT / 100 * (n_resamples - 1))
    high_rank = round(CI_HIGH_PCT / 100 * (n_resamples - 1))
    ci_low = resampled_gaps[low_rank]
    ci_high = resampled_gaps[high_rank]

    return {
        "n_items": n,
        "n_resamples": n_resamples,
        "score_a": sum(outcomes_a) / n,
        "score_b": sum(outcomes_b) / n,
        "observed_gap": observed_gap,
        "ci_95_low": ci_low,
        "ci_95_high": ci_high,
        "ci_excludes_zero": ci_low > 0 or ci_high < 0,
    }


def run(seed: int) -> dict:
    large_a, large_b = generate_paired_outcomes(
        n_items=300, true_effect=TRUE_EFFECT, seed=seed
    )
    large_result = paired_bootstrap_ci(
        large_a, large_b, n_resamples=N_RESAMPLES, seed=seed + 1
    )

    small_a, small_b = generate_paired_outcomes(
        n_items=25, true_effect=TRUE_EFFECT, seed=seed + 2
    )
    small_result = paired_bootstrap_ci(
        small_a, small_b, n_resamples=N_RESAMPLES, seed=seed + 3
    )

    return {
        "seed": seed,
        "true_effect": TRUE_EFFECT,
        "large_n": large_result,
        "small_n": small_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=str, default="../runs/bootstrap-run.json")
    args = parser.parse_args()

    result = run(args.seed)

    print(f"true_effect (A - B, by construction): {result['true_effect']:.4f}")
    for label in ("large_n", "small_n"):
        r = result[label]
        print(
            f"[{label}] n={r['n_items']} score_a={r['score_a']:.4f} "
            f"score_b={r['score_b']:.4f} observed_gap={r['observed_gap']:.4f} "
            f"95% CI=({r['ci_95_low']:.4f}, {r['ci_95_high']:.4f}) "
            f"excludes_zero={r['ci_excludes_zero']}"
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
