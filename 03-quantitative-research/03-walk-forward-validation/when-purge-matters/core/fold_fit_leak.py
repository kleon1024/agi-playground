"""Where purging actually matters: per-fold selection under label overlap.

The stage's recorded run fit one fixed linear rule per fold and found no
leakage uplift — the note says so explicitly, because a rule with no
selection power has nothing for the label overlap to leak. This script gives
the fold real selection power: for every fold it tries a grid of thresholds
on the linear prediction, keeps the threshold with the best *in-fold* Sharpe,
and evaluates out-of-fold. That is how a researcher actually searches a rule,
and it is the regime where an unpurged split (overlapping five-day labels
across the train/test boundary) inflates the out-of-fold number relative to a
purged and gapped split.

Everything is imported from the stage's core: the same AAPL fetch, the same
five-day labels, the same walk-forward splitters. Only the per-fold selection
is new.

Run:
    uv run python core/fold_fit_leak.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from walk_forward import (
    LABEL_DAYS,
    LOOKBACK_DAYS,
    Example,
    Split,
    fetch_price_history,
    fit_linear,
    sharpe,
    walk_forward_splits,
)

THRESHOLDS = (-0.02, -0.01, -0.005, 0.0, 0.005, 0.01, 0.02, 0.05, 0.1)


def examples_from_closes_with_label(closes: list[float], label_days: int) -> list[Example]:
    return [
        Example(
            feature=closes[index] / closes[index - LOOKBACK_DAYS] - 1,
            forward_return=closes[index + label_days] / closes[index] - 1,
        )
        for index in range(LOOKBACK_DAYS, len(closes) - label_days)
    ]


def rule_returns(
    examples: list[Example],
    indices: list[int],
    intercept: float,
    slope: float,
    threshold: float,
) -> list[float]:
    out = []
    for index in indices:
        prediction = intercept + slope * examples[index].feature
        position = 1.0 if prediction >= threshold else -1.0
        out.append(position * examples[index].forward_return)
    return out


def fold_returns_with_selection(examples: list[Example], split: Split) -> tuple[list[float], float]:
    """Fit one linear rule, select the threshold by in-fold Sharpe, return the
    out-of-fold returns and the chosen threshold."""
    intercept, slope = fit_linear(examples, split.train)
    best_threshold, best_sharpe = THRESHOLDS[0], -math.inf
    for threshold in THRESHOLDS:
        in_fold = sharpe(rule_returns(examples, split.train, intercept, slope, threshold))
        if in_fold > best_sharpe:
            best_threshold, best_sharpe = threshold, in_fold
    out_of_fold = rule_returns(examples, split.test, intercept, slope, best_threshold)
    return out_of_fold, best_threshold


def main() -> None:
    bars, _dividends, _splits = fetch_price_history("AAPL", "5y")
    closes = [bar.adjclose if bar.adjclose is not None else bar.close for bar in bars]
    print(f"bars: {len(closes)}")

    for label_days in (LABEL_DAYS, 20):
        examples = examples_from_closes_with_label(closes, label_days)
        print(f"\n### label days = {label_days} ({len(examples)} examples)")
        for label, purge, gap in (("chronological, unpurged", 0, 0), ("purged + gapped", label_days, label_days)):
            splits = walk_forward_splits(len(examples), 5, purge=purge, gap=gap)
            all_oof: list[float] = []
            boundary: list[float] = []
            interior: list[float] = []
            print(f"\n== {label} ==")
            for fold, split in enumerate(splits):
                returns, chosen = fold_returns_with_selection(examples, split)
                all_oof.extend(returns)
                overlap_floor = split.test[0] + label_days
                for index, value in zip(split.test, returns):
                    (boundary if index < overlap_floor else interior).append(value)
                in_fold_sharpe = max(
                    sharpe(rule_returns(examples, split.train, *fit_linear(examples, split.train), t))
                    for t in THRESHOLDS
                )
                print(
                    f"  fold {fold}: train={len(split.train)} test={len(split.test)} "
                    f"chosen threshold={chosen:+.3f} in-fold Sharpe={in_fold_sharpe:.3f} "
                    f"out-of-fold Sharpe={sharpe(returns):.3f}"
                )
            print(f"  aggregate out-of-fold Sharpe: {sharpe(all_oof):.4f}")
            print(
                f"  boundary rows ({len(boundary)}): Sharpe {sharpe(boundary):.4f}  |  "
                f"interior rows ({len(interior)}): Sharpe {sharpe(interior):.4f}"
            )


if __name__ == "__main__":
    main()
