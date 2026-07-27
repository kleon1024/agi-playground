"""The same job as `core/interactions.py`, built on pandas.

Requires: pip install pandas

A production data-prep job does not write a `for` loop over Python objects for
a few million rows; it vectorizes. This script does the identical eligibility
filter, time split, and popularity baseline as `core/interactions.py`, using
`groupby`, boolean masks, and `searchsorted` instead of hand-written loops and
dictionaries. The output is the same on the same input — the difference is
implementation, not policy. Nothing here changes what "eligible" or "the
cutoff" means; it changes how fast you can compute them.

This is also where a real pipeline would plug in a maintained chrono-split
utility (for example `recommenders.datasets.python_splitters` or `lenskit`'s
splitting module) instead of the four lines below. They implement exactly this
cutoff-by-timestamp logic; reading the four lines here is what makes it
obvious there is nothing more to those utilities than that.

Run:  python pandas_pipeline.py ratings.csv --k 20
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def load(path: Path) -> tuple[pd.DataFrame, int]:
    """Load a MovieLens-style ratings CSV: userId,movieId,rating,timestamp."""
    raw = pd.read_csv(path, header=0, names=["user", "item", "rating", "timestamp"])
    before = len(raw)
    numeric = pd.to_numeric(raw["rating"], errors="coerce")
    ts = pd.to_numeric(raw["timestamp"], errors="coerce")
    frame = raw.assign(rating=numeric, timestamp=ts).dropna(subset=["rating", "timestamp"])
    return frame, before - len(frame)


def clean(frame: pd.DataFrame, min_user: int = 5, min_item: int = 5, max_passes: int = 5) -> pd.DataFrame:
    """Drop duplicate rows, then iteratively enforce minimum interaction counts."""
    current = frame.drop_duplicates(subset=["user", "item", "timestamp"])
    for _ in range(max_passes):
        user_ok = current.groupby("user")["item"].transform("size") >= min_user
        item_ok = current.groupby("item")["user"].transform("size") >= min_item
        filtered = current[user_ok & item_ok]
        if len(filtered) == len(current):
            return filtered
        current = filtered
    return current


def time_split(frame: pd.DataFrame, test_fraction: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    """Identical contract to `core.interactions.time_split`: one global cutoff."""
    ordered = frame.sort_values("timestamp")
    cutoff_index = min(len(ordered) - 1, max(0, int(len(ordered) * (1 - test_fraction))))
    cutoff_ts = float(ordered["timestamp"].iloc[cutoff_index])
    train = frame[frame["timestamp"] < cutoff_ts]
    test = frame[frame["timestamp"] >= cutoff_ts]
    return train, test, cutoff_ts


def leakage_rate(train: pd.DataFrame, test: pd.DataFrame) -> tuple[int, int]:
    """Vectorized equivalent of `core.interactions.leakage_rate`."""
    latest_train_ts = train.groupby("user")["timestamp"].max()
    joined = test.join(latest_train_ts.rename("latest_train_ts"), on="user")
    eligible = joined["latest_train_ts"].notna()
    leaked = eligible & (joined["latest_train_ts"] > joined["timestamp"])
    return int(leaked.sum()), int(eligible.sum())


def popularity_ranking(train: pd.DataFrame) -> pd.Index:
    return train["item"].value_counts().sort_values(ascending=False).index


def hit_rate_at_k(ranking: pd.Index, test: pd.DataFrame, k: int) -> float:
    if len(test) == 0:
        return 0.0
    top_k = set(ranking[:k])
    return float(test["item"].isin(top_k).mean())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path)
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--min-user", type=int, default=5)
    parser.add_argument("--min-item", type=int, default=5)
    parser.add_argument("--k", type=int, default=20)
    args = parser.parse_args()

    frame, malformed = load(args.path)
    cleaned = clean(frame, args.min_user, args.min_item)
    print(f"malformed, dropped        {malformed}")
    print(f"eligible interactions      {len(cleaned)}")

    train, test, cutoff = time_split(cleaned, args.test_fraction)
    leaked, eligible = leakage_rate(train, test)
    print(f"\ntime split  cutoff={cutoff:.2f}  train={len(train)}  test={len(test)}")
    print(f"  future leakage: {leaked}/{eligible}")

    ranking = popularity_ranking(train)
    print(f"popularity hit-rate@{args.k}: {hit_rate_at_k(ranking, test, args.k):.4f}")
    print("\nSame contract as core/interactions.py — verify the two agree on the")
    print("same input file before trusting either on data core/ cannot handle.")


if __name__ == "__main__":
    main()
