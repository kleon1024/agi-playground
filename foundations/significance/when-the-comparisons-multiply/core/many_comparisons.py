"""Twelve comparisons, declared alpha, and the ones that fire by chance.

The significance chapter compares two models and asks whether the gap is
real. Production evaluation compares many pairs at once -- several model
variants against a baseline, several prompts, several tasks. Every
comparison carries its own chance of a false positive, so more comparisons
means a higher chance that at least one of them fires by itself.

This script runs paired z-tests on synthetic per-item differences under two
shapes:

1. Null experiment: all 12 pairs have a true effect of zero. Naive testing
   at alpha 0.05 flags a handful by chance; the family-wise probability
   that at least one fires is 1 - 0.95**12 = 46.0 percent.
2. Planted experiment: pair 6 carries a true effect. Naive testing flags it
   plus a few chance nulls; Benjamini-Hochberg at q = 0.10 keeps the true
   pair and suppresses the chance hits.

Then it repeats the planted experiment 500 times and measures the false
discovery behavior of both procedures under repetition, not just one draw.

Run:
    uv run python core/many_comparisons.py
"""

from __future__ import annotations

import math
import random

N_PAIRS = 12
N_ITEMS = 300
PLANTED_INDEX = 6  # which pair carries the true effect in experiment B
TRUE_EFFECT = 0.25  # per-item standard deviation, effect size
ALPHA = 0.05
Q = 0.10
REPEATS = 500
SEED = 39


def z_test_pvalue(diffs: list[float]) -> float:
    """Two-sided p-value for a paired z-test on per-item differences."""
    n = len(diffs)
    mean = sum(diffs) / n
    var = sum((d - mean) ** 2 for d in diffs) / (n - 1)
    if var == 0.0:
        return 1.0
    z = abs(mean) / math.sqrt(var / n)
    return 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))


def draw_experiment(
    rng: random.Random, planted: bool
) -> list[tuple[float, bool]]:
    """Return (p-value, is_true_positive) for each of the 12 pairs."""
    rows: list[tuple[float, bool]] = []
    for i in range(N_PAIRS):
        true = planted and i == PLANTED_INDEX
        mu = TRUE_EFFECT if true else 0.0
        diffs = [rng.gauss(mu, 1.0) for _ in range(N_ITEMS)]
        rows.append((z_test_pvalue(diffs), true))
    return rows


def naive_verdicts(rows: list[tuple[float, bool]]) -> list[bool]:
    return [p < ALPHA for p, _ in rows]


def bh_verdicts(rows: list[tuple[float, bool]]) -> list[bool]:
    """Benjamini-Hochberg at q; returns rejected flags in original order."""
    order = sorted(range(len(rows)), key=lambda i: rows[i][0])
    m = len(rows)
    largest_kept = -1
    for rank, idx in enumerate(order, start=1):
        if rows[idx][0] <= (rank * Q) / m:
            largest_kept = rank
    keep = {order[i] for i in range(largest_kept)}
    return [i in keep for i in range(m)]


def fmt_p(p: float) -> str:
    return f"{p:.4f}" if p >= 1e-3 else f"{p:.2e}"


def main() -> None:
    rng = random.Random(SEED)

    # Experiment A: all twelve pairs null, one illustrative draw.
    null_rows = draw_experiment(rng, planted=False)
    null_naive = naive_verdicts(null_rows)
    null_bh = bh_verdicts(null_rows)
    print(
        "null experiment: all 12 pairs have true effect zero, one draw, "
        f"n={N_ITEMS} items each"
    )
    print(f"  naive alpha={ALPHA} flags {sum(null_naive)} of 12 by chance")
    print(
        f"  expected under the null: {N_PAIRS*ALPHA:.1f}; "
        f"P(at least one) = 1 - 0.95^{N_PAIRS} = {100*(1-0.95**N_PAIRS):.1f}%"
    )
    print(f"  BH q={Q} flags {sum(null_bh)} of 12")
    print()

    # Experiment B: pair 6 planted, one illustrative draw with a table.
    planted_rows = draw_experiment(rng, planted=True)
    naive = naive_verdicts(planted_rows)
    bh = bh_verdicts(planted_rows)
    print(
        f"planted experiment: pair {PLANTED_INDEX} carries true effect "
        f"{TRUE_EFFECT}, one draw"
    )
    print(
        f"  {'pair':>4} {'p-value':>10} {'naive':>7} "
        f"{'BH q=0.10':>10}  true?"
    )
    for i, (p, true) in enumerate(planted_rows):
        print(
            f"  {i:>4} {fmt_p(p):>10} "
            f"{'reject' if naive[i] else 'keep':>7} "
            f"{'reject' if bh[i] else 'keep':>10}  {true}"
        )
    print(f"  naive rejects {sum(naive)}; BH rejects {sum(bh)}")
    print()

    # Repetition: 500 draws of the planted shape.
    naive_fp = 0
    bh_fp = 0
    naive_missed_true = 0
    bh_missed_true = 0
    experiments_with_naive_fp = 0
    experiments_with_bh_fp = 0
    for _ in range(REPEATS):
        rows = draw_experiment(rng, planted=True)
        n_naive = naive_verdicts(rows)
        n_bh = bh_verdicts(rows)
        naive_fp += sum(n_naive[i] for i in range(N_PAIRS) if not rows[i][1])
        bh_fp += sum(n_bh[i] for i in range(N_PAIRS) if not rows[i][1])
        if not n_naive[PLANTED_INDEX]:
            naive_missed_true += 1
        if not n_bh[PLANTED_INDEX]:
            bh_missed_true += 1
        if any(n_naive[i] for i in range(N_PAIRS) if not rows[i][1]):
            experiments_with_naive_fp += 1
        if any(n_bh[i] for i in range(N_PAIRS) if not rows[i][1]):
            experiments_with_bh_fp += 1

    print(f"{REPEATS} experiments, planted shape (11 null + 1 true):")
    print(
        f"  mean false positives per experiment: naive {naive_fp/REPEATS:.2f} "
        f"vs BH {bh_fp/REPEATS:.2f}"
    )
    print(
        "  share of experiments with at least one false positive (naive): "
        f"{100*experiments_with_naive_fp/REPEATS:.1f}% "
        f"(theory for 11 nulls: {100*(1-0.95**11):.1f}%)"
    )
    print(
        "  share of experiments with at least one false positive (BH): "
        f"{100*experiments_with_bh_fp/REPEATS:.1f}%"
    )
    print(
        f"  true pair missed: naive {naive_missed_true}/"
        f"{REPEATS}, BH {bh_missed_true}/{REPEATS}"
    )
    print(
        f"  verdict: naive fires ~{naive_fp/REPEATS:.1f} false positives per "
        "experiment; BH q=0.10"
    )
    print(
        f"  cuts that to ~{bh_fp/REPEATS:.2f} while keeping the planted "
        "effect almost always."
    )


if __name__ == "__main__":
    main()
