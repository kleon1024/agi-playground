"""Purged walk-forward validation with a distribution-aware Sharpe correction.

``TimeSeriesSplit`` preserves order and its ``gap`` parameter can remove a
fixed number of rows before a test block. It cannot infer when each label's
forward window ends, and therefore cannot decide which training labels overlap
the test information set. This wrapper makes that ownership explicit.

Requires: numpy, scipy, scikit-learn
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np
from scipy import stats
from sklearn.model_selection import TimeSeriesSplit

EULER_MASCHERONI = 0.5772156649015329


@dataclass(frozen=True)
class Fold:
    train: np.ndarray
    test: np.ndarray


class PurgedEmbargoedSplit:
    """Expanding-window splits with label-aware purge and boundary embargo."""

    def __init__(
        self,
        *,
        n_splits: int = 5,
        test_size: int | None = None,
        embargo: int = 0,
    ) -> None:
        if n_splits < 2:
            raise ValueError("n_splits must be at least 2")
        if embargo < 0:
            raise ValueError("embargo must be non-negative")
        self.n_splits = n_splits
        self.test_size = test_size
        self.embargo = embargo

    def split(self, label_end: np.ndarray) -> Iterator[Fold]:
        """Yield folds after removing training labels that touch test data.

        ``label_end[i]`` is the final sample index consumed by row ``i``'s
        target. This is stronger than a generic fixed gap because labels may
        have different horizons. With strict past-only training, a post-test
        embargo cannot remove a same-fold training row; the declared embargo
        is therefore applied as an additional pre-test boundary gap.
        """
        label_end = np.asarray(label_end, dtype=int)
        base = TimeSeriesSplit(n_splits=self.n_splits, test_size=self.test_size)
        for train, test in base.split(np.empty(len(label_end))):
            test_start = int(test[0])
            overlaps_test = label_end[train] >= test_start
            inside_embargo = train >= test_start - self.embargo
            keep = ~(overlaps_test | inside_embargo)
            yield Fold(train=train[keep], test=test)


def annualized_sharpe(returns: np.ndarray, periods: int = 252) -> float:
    returns = np.asarray(returns, dtype=float)
    if returns.size < 2:
        raise ValueError("at least two returns are required")
    standard_deviation = float(returns.std(ddof=1))
    if standard_deviation == 0:
        raise ValueError("Sharpe is undefined for zero-variance returns")
    return float(math.sqrt(periods) * returns.mean() / standard_deviation)


def expected_maximum_sharpe(
    *,
    trial_count: int,
    sharpe_standard_error: float,
) -> float:
    """Expected maximum under independent Gaussian null Sharpe estimates."""
    if trial_count < 1:
        raise ValueError("trial_count must be positive")
    if trial_count == 1:
        return 0.0
    first = stats.norm.ppf(1 - 1 / trial_count)
    second = stats.norm.ppf(1 - 1 / (trial_count * math.e))
    return float(
        sharpe_standard_error
        * ((1 - EULER_MASCHERONI) * first + EULER_MASCHERONI * second)
    )


def deflated_sharpe_probability(
    returns: np.ndarray,
    *,
    trial_count: int,
    periods: int = 252,
) -> float:
    """Probability that observed Sharpe clears the search-induced benchmark.

    This is the Bailey and López de Prado probabilistic-Sharpe form with the
    benchmark replaced by the expected maximum across the disclosed trials.
    Correlated trials require an estimated effective trial count; raw grid
    size is not automatically the correct input.
    """
    returns = np.asarray(returns, dtype=float)
    observed = annualized_sharpe(returns, periods=periods)
    sample_size = returns.size
    skew = float(stats.skew(returns, bias=False))
    kurtosis = float(stats.kurtosis(returns, fisher=False, bias=False))
    sharpe_se = math.sqrt(
        max(1e-12, (1 - skew * observed + ((kurtosis - 1) / 4) * observed**2) / (sample_size - 1))
    )
    benchmark = expected_maximum_sharpe(
        trial_count=trial_count,
        sharpe_standard_error=sharpe_se,
    )
    return float(stats.norm.cdf((observed - benchmark) / sharpe_se))


def main() -> None:
    rng = np.random.default_rng(20260727)
    returns = rng.normal(0.0002, 0.01, size=1_250)
    horizon = 5
    label_end = np.minimum(np.arange(returns.size) + horizon, returns.size - 1)
    splitter = PurgedEmbargoedSplit(n_splits=5, embargo=5)
    folds = list(splitter.split(label_end))
    probability = deflated_sharpe_probability(returns, trial_count=14)
    print(f"folds={len(folds)} first_train={len(folds[0].train)} first_test={len(folds[0].test)}")
    print(f"illustrative deflated-Sharpe probability={probability:.4f}")


if __name__ == "__main__":
    main()
