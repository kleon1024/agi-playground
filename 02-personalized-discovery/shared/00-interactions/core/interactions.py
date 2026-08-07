"""From-scratch interaction dataset preparation: load, clean, split by time.

Everything here is pure standard library, on purpose. The point of this stage
is not clever code; it is that the split boundary is a single timestamp, and
every mistake downstream traces back to this one file if it is wrong.

Three things this module measures for any interaction log you hand it:

1. how many rows survive basic eligibility checks (parses, not a duplicate,
   user and item seen enough times to be evaluable at all);
2. whether a time-ordered split and a random split disagree on how much of a
   user's own future leaks into their own training rows;
3. how a popularity-only ranking performs against each split, which is the
   floor every later stage in this mission has to clear.

Run against a real MovieLens-style ratings file:

    python interactions.py ratings.csv --k 20

Or run the offline demo, which needs no download and no network:

    python interactions.py --synthetic 5000
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Interaction:
    user: str
    item: str
    timestamp: float
    rating: float | None = None


# --- 1. Eligibility, before any quality judgment ----------------------------
#
# Eligibility asks "can this row even be used?" A row that fails to parse, a
# duplicate of one already seen, or a user/item too sparse to hold out a test
# interaction for is not a quality problem — it is not usable data yet. Quality
# judgments (is this rating trustworthy, is this user a bot) come after, and
# this mini pipeline stops at eligibility because that is already where most
# of the damage of a bad split happens.


def read_movielens_ratings(path: Path) -> tuple[list[Interaction], int]:
    """Parse a MovieLens-style `ratings.csv`: userId,movieId,rating,timestamp.

    Also accepts any four-column file with that shape. Returns the parsed
    interactions and a count of rows dropped for failing to parse.
    """
    interactions: list[Interaction] = []
    malformed = 0
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        first = next(reader, None)
        if first is not None and not _looks_like_header(first):
            handle.seek(0)
            reader = csv.reader(handle)
        for row in reader:
            if len(row) < 4:
                malformed += 1
                continue
            try:
                interactions.append(
                    Interaction(
                        user=row[0],
                        item=row[1],
                        rating=float(row[2]),
                        timestamp=float(row[3]),
                    )
                )
            except ValueError:
                malformed += 1
    return interactions, malformed


def _looks_like_header(row: list[str]) -> bool:
    try:
        float(row[2])
        float(row[3])
    except (ValueError, IndexError):
        return True
    return False


def dedupe(interactions: list[Interaction]) -> list[Interaction]:
    """Drop exact repeats of (user, item, timestamp).

    A repeat this exact is a logging artifact, not a second event — keeping it
    lets one client-side retry count as two units of user preference.
    """
    seen: set[tuple[str, str, float]] = set()
    kept: list[Interaction] = []
    for row in interactions:
        key = (row.user, row.item, row.timestamp)
        if key in seen:
            continue
        seen.add(key)
        kept.append(row)
    return kept


def filter_min_interactions(
    interactions: list[Interaction],
    min_user_interactions: int = 5,
    min_item_interactions: int = 5,
    max_passes: int = 5,
) -> list[Interaction]:
    """Iteratively drop users and items below a minimum interaction count.

    This is a fixed point, not a single pass: removing a sparse item can drop
    a user below threshold, and removing that user can drop another item.
    `max_passes` bounds the loop; on real logs it converges in two or three.
    """
    current = interactions
    for _ in range(max_passes):
        user_counts = Counter(row.user for row in current)
        item_counts = Counter(row.item for row in current)
        filtered = [
            row
            for row in current
            if user_counts[row.user] >= min_user_interactions
            and item_counts[row.item] >= min_item_interactions
        ]
        if len(filtered) == len(current):
            return filtered
        current = filtered
    return current


# --- 2. The split that matters -----------------------------------------------


def time_split(
    interactions: list[Interaction], test_fraction: float = 0.2
) -> tuple[list[Interaction], list[Interaction], float]:
    """Split by a single global timestamp cutoff, not by row or by user.

    Every interaction strictly before the cutoff is train; every interaction
    at or after it is test. No row's user, item, or index matters — only when
    it happened relative to everything else in the log.
    """
    if not interactions:
        return [], [], 0.0
    ordered = sorted(interactions, key=lambda row: row.timestamp)
    cutoff_index = min(len(ordered) - 1, max(0, int(len(ordered) * (1 - test_fraction))))
    cutoff_ts = ordered[cutoff_index].timestamp
    train = [row for row in interactions if row.timestamp < cutoff_ts]
    test = [row for row in interactions if row.timestamp >= cutoff_ts]
    return train, test, cutoff_ts


def random_split(
    interactions: list[Interaction], test_fraction: float = 0.2, seed: int = 0
) -> tuple[list[Interaction], list[Interaction]]:
    """The wrong split, built the way it usually gets built: shuffle, cut.

    Exists only as a contrast object for `leakage_rate` below. Nothing in this
    module recommends using it.
    """
    rng = random.Random(seed)
    shuffled = list(interactions)
    rng.shuffle(shuffled)
    cutoff = int(len(shuffled) * (1 - test_fraction))
    return shuffled[:cutoff], shuffled[cutoff:]


def leakage_rate(
    train: list[Interaction], test: list[Interaction]
) -> tuple[int, int]:
    """Count test rows whose own user has a *later* interaction sitting in train.

    If a user's train set contains something that happened after a test event
    for that same user, the model can learn correlations that only exist
    because it has already seen the user's future. For a proper time split
    this is zero by construction: every train timestamp is below the cutoff
    and every test timestamp is at or above it, so no train row can ever be
    later than a test row. For a random split it generally is not zero,
    because shuffling erases the order the split is supposed to respect.

    Returns (leaked_count, eligible_count), where eligible counts test rows
    whose user also appears in train at all.
    """
    latest_train_ts: dict[str, float] = defaultdict(lambda: float("-inf"))
    for row in train:
        latest_train_ts[row.user] = max(latest_train_ts[row.user], row.timestamp)
    leaked = 0
    eligible = 0
    for row in test:
        if row.user not in latest_train_ts:
            continue
        eligible += 1
        if latest_train_ts[row.user] > row.timestamp:
            leaked += 1
    return leaked, eligible


# --- 3. The floor every later stage must clear -------------------------------


def popularity_ranking(train: list[Interaction]) -> list[str]:
    """Rank items by raw interaction count in train. No personalization at all."""
    counts = Counter(row.item for row in train)
    return [item for item, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def hit_rate_at_k(ranking: list[str], test: list[Interaction], k: int) -> float:
    """Fraction of test interactions whose item is in the top-k of `ranking`."""
    if not test:
        return 0.0
    top_k = set(ranking[:k])
    hits = sum(1 for row in test if row.item in top_k)
    return hits / len(test)


# --- offline demo -------------------------------------------------------------


def synthetic_interactions(n_users: int = 200, n_items: int = 50, n_events: int = 4000, seed: int = 0) -> list[Interaction]:
    """A small deterministic event stream, for running this file with no dataset.

    Item popularity follows a rank-based skew so a popularity baseline has
    something real to exploit, matching the shape of real interaction logs.
    This is illustrative fixture data, not a claim about any real platform.
    """
    rng = random.Random(seed)
    item_weights = [1.0 / (rank + 1) for rank in range(n_items)]
    events: list[Interaction] = []
    clock = 0.0
    for _ in range(n_events):
        user = f"u{rng.randrange(n_users)}"
        item = f"i{rng.choices(range(n_items), weights=item_weights, k=1)[0]}"
        clock += rng.uniform(0.5, 5.0)
        events.append(Interaction(user=user, item=item, rating=float(rng.randint(1, 5)), timestamp=clock))
    return events


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", nargs="?", type=Path, help="MovieLens-style ratings CSV")
    parser.add_argument("--synthetic", type=int, default=0, metavar="N", help="ignore PATH, generate N demo events")
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--min-user", type=int, default=5)
    parser.add_argument("--min-item", type=int, default=5)
    parser.add_argument("--k", type=int, default=20)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    if args.synthetic:
        print(f"[demo] generating {args.synthetic} synthetic events — illustrative only, not a real dataset")
        raw = synthetic_interactions(n_events=args.synthetic, seed=args.seed)
        malformed = 0
    else:
        if args.path is None:
            parser.error("provide a ratings CSV path, or --synthetic N for an offline demo")
        raw, malformed = read_movielens_ratings(args.path)

    deduped = dedupe(raw)
    cleaned = filter_min_interactions(deduped, args.min_user, args.min_item)

    print(f"raw rows                       {len(raw)}")
    print(f"malformed, dropped             {malformed}")
    print(f"exact duplicates, dropped      {len(raw) - len(deduped)}")
    print(f"below min-interactions, dropped {len(deduped) - len(cleaned)}")
    print(f"eligible interactions          {len(cleaned)}")

    train_t, test_t, cutoff = time_split(cleaned, args.test_fraction)
    train_r, test_r = random_split(cleaned, args.test_fraction, args.seed)

    leaked_t, eligible_t = leakage_rate(train_t, test_t)
    leaked_r, eligible_r = leakage_rate(train_r, test_r)

    print(f"\ntime split    cutoff={cutoff:.2f}  train={len(train_t)}  test={len(test_t)}")
    print(f"  future leakage: {leaked_t}/{eligible_t} test rows precede a same-user train row")
    print(f"random split  train={len(train_r)}  test={len(test_r)}")
    print(f"  future leakage: {leaked_r}/{eligible_r} test rows precede a same-user train row")

    ranking_t = popularity_ranking(train_t)
    ranking_r = popularity_ranking(train_r)
    print(f"\npopularity hit-rate@{args.k}")
    print(f"  time split:   {hit_rate_at_k(ranking_t, test_t, args.k):.4f}")
    print(f"  random split: {hit_rate_at_k(ranking_r, test_r, args.k):.4f}")
    print("\nThese numbers describe only this run. Nothing here is recorded — that")
    print("happens in a runs/ entry once this stage is actually evaluated end to end.")


if __name__ == "__main__":
    main()
