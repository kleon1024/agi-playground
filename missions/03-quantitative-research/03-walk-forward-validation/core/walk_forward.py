"""Leakage comparison with folds that actually own model fitting.

The signal is a fixed trailing-return feature. Each fold fits one linear rule
on its training rows, then takes the sign of the predicted forward return on
the test rows. The three splitters therefore change what the rule can learn:

* shuffled k-fold admits future observations;
* chronological walk-forward uses only the past but leaves overlapping labels
  at the boundary;
* protected walk-forward removes the label overlap and an additional gap.

The constants were selected before execution, not tuned for a descending
demonstration. The public AAPL path comes from stage 00.
"""

from __future__ import annotations

import math
import random
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "00-market-data" / "core"))
from point_in_time import fetch_price_history

LABEL_DAYS = 5
LOOKBACK_DAYS = 20
FOLDS = 5
SHUFFLE_SEED = 20260727


@dataclass(frozen=True)
class Example:
    feature: float
    forward_return: float


@dataclass(frozen=True)
class Split:
    train: list[int]
    test: list[int]


def sharpe(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    deviation = statistics.stdev(values)
    return 0.0 if deviation == 0 else statistics.mean(values) / deviation * math.sqrt(252 / LABEL_DAYS)


def examples_from_closes(closes: list[float]) -> list[Example]:
    return [
        Example(
            feature=closes[index] / closes[index - LOOKBACK_DAYS] - 1,
            forward_return=closes[index + LABEL_DAYS] / closes[index] - 1,
        )
        for index in range(LOOKBACK_DAYS, len(closes) - LABEL_DAYS)
    ]


def fit_linear(examples: list[Example], indices: list[int]) -> tuple[float, float]:
    """Fit y = intercept + slope*x using only one fold's training indices."""
    if len(indices) < 2:
        raise ValueError("a fold needs at least two training observations")
    x_mean = statistics.mean(examples[index].feature for index in indices)
    y_mean = statistics.mean(examples[index].forward_return for index in indices)
    numerator = sum(
        (examples[index].feature - x_mean) * (examples[index].forward_return - y_mean)
        for index in indices
    )
    denominator = sum((examples[index].feature - x_mean) ** 2 for index in indices)
    slope = numerator / denominator if denominator else 0.0
    return y_mean - slope * x_mean, slope


def fold_returns(examples: list[Example], split: Split) -> list[float]:
    intercept, slope = fit_linear(examples, split.train)
    output = []
    for index in split.test:
        prediction = intercept + slope * examples[index].feature
        position = 1.0 if prediction >= 0 else -1.0
        output.append(position * examples[index].forward_return)
    return output


def shuffled_splits(n_samples: int, n_splits: int, seed: int) -> list[Split]:
    """Invalid comparator: every training set contains later observations."""
    shuffled = list(range(n_samples))
    random.Random(seed).shuffle(shuffled)
    buckets = [shuffled[offset::n_splits] for offset in range(n_splits)]
    output = []
    for fold, test in enumerate(buckets):
        train = [index for other, bucket in enumerate(buckets) if other != fold for index in bucket]
        output.append(Split(train=sorted(train), test=sorted(test)))
    return output


def walk_forward_splits(
    n_samples: int,
    n_splits: int,
    *,
    purge: int,
    gap: int,
) -> list[Split]:
    """Expanding-window folds with label-aware purge and an extra boundary gap.

    In a strict walk-forward evaluation no post-test row belongs to the same
    fold's training set. The finance literature's post-test embargo therefore
    becomes a pre-test gap here: the next test block starts only after the
    declared boundary margin. Purge owns label overlap; ``gap`` owns residual
    serial dependence. They remain separate controls.
    """
    initial_train = n_samples // 2
    test_width = (n_samples - initial_train) // n_splits
    output = []
    for fold in range(n_splits):
        test_start = initial_train + fold * test_width
        test_end = n_samples if fold == n_splits - 1 else test_start + test_width
        train_end = max(0, test_start - purge - gap)
        output.append(
            Split(
                train=list(range(train_end)),
                test=list(range(test_start, test_end)),
            )
        )
    return output


def evaluate(examples: list[Example], splits: list[Split]) -> tuple[float, list[float]]:
    returns = [value for split in splits for value in fold_returns(examples, split)]
    return sharpe(returns), returns


def deflated_sharpe(observed: float, trials: int, samples: int) -> float:
    """Teaching approximation; prod/ implements the distribution-aware form."""
    expected_max_noise = math.sqrt(2 * math.log(max(1, trials)) / max(1, samples))
    expected_max_noise *= math.sqrt(252 / LABEL_DAYS)
    return observed - expected_max_noise


def main() -> None:
    bars, _dividends, _splits = fetch_price_history("AAPL", "5y")
    closes = [bar.adjclose if bar.adjclose is not None else bar.close for bar in bars]
    examples = examples_from_closes(closes)

    invalid_splits = shuffled_splits(len(examples), FOLDS, SHUFFLE_SEED)
    chronological_splits = walk_forward_splits(len(examples), FOLDS, purge=0, gap=0)
    protected_splits = walk_forward_splits(
        len(examples),
        FOLDS,
        purge=LABEL_DAYS,
        gap=LABEL_DAYS,
    )
    invalid, invalid_returns = evaluate(examples, invalid_splits)
    chronological, chronological_returns = evaluate(examples, chronological_splits)
    protected, protected_returns = evaluate(examples, protected_splits)

    print(f"bars={len(closes)} usable labels={len(examples)} label window={LABEL_DAYS}d")
    print(f"shuffled-invalid out-of-fold Sharpe={invalid:.4f}")
    print(f"chronological-unpurged out-of-fold Sharpe={chronological:.4f}")
    print(
        f"purged-{LABEL_DAYS}d-gapped-{LABEL_DAYS}d out-of-fold Sharpe="
        f"{protected:.4f}"
    )
    print(
        "deflated Sharpe (14 disclosed trials)="
        f"{deflated_sharpe(protected, 14, len(protected_returns)):.4f}"
    )
    print(
        "fold 1 train/test sizes",
        len(protected_splits[0].train),
        len(protected_splits[0].test),
    )
    print(
        "evaluated returns shuffled/chronological/protected",
        len(invalid_returns),
        len(chronological_returns),
        len(protected_returns),
    )


if __name__ == "__main__":
    main()
