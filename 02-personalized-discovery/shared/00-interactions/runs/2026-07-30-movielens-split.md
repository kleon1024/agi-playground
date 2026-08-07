# Run — stage 00 interactions, MovieLens split and leakage comparison

**Date:** 2026-07-30
**Hardware:** Apple Silicon (arm64), 10 cores, macOS (Darwin 24.6.0). CPU-only;
no GPU involved anywhere in this stage.
**Cost:** \$0 (local lane, stdlib only).

## Input

MovieLens `ml-latest-small`, downloaded from
`https://files.grouplens.org/datasets/movielens/ml-latest-small.zip`:
100,836 ratings, 610 users, 9,724 movies, timestamps from 1996 to 2018.

## Command

```bash
python core/interactions.py ratings.csv --k 20
```

## Output

```
raw rows                       100836
malformed, dropped             0
exact duplicates, dropped      0
below min-interactions, dropped 10562
eligible interactions          90274

time split    cutoff=1450867829.00  train=72219  test=18055
  future leakage: 0/1223 test rows precede a same-user train row
random split  train=72219  test=18055
  future leakage: 17885/18055 test rows precede a same-user train row

popularity hit-rate@20
  time split:   0.0389
  random split: 0.0496
```

## Distribution and sample evidence (ad hoc script against `core/interactions.py`)

Interactions-per-user, after `filter_min_interactions` (610 users, default
`min_user=5, min_item=5`):

```
bucket     users
10-19          8
20-49        224
50-99        139
100-199      116
200+         123
```

Median 68, min 12, max 2,132.

`filter_min_interactions` drops 10,562 rows, all of them for item-sparsity:
6,074 of 9,724 movies have fewer than 5 ratings. Every user in this dataset
starts with at least 20 ratings by MovieLens's own construction, but removing
sparse items can still push a user below that floor: 8 users do, including
user 175 (24 -> 12), user 598 (21 -> 16), and user 578 (27 -> 17).

A concrete random-split leak: user 75's test row is timestamped
`1158989870`; that same user's random-split train set contains a row
timestamped `1158990239` — 369 seconds later than the "test" event it is
meant to predict.

A parsed row, verbatim: `Interaction(user='1', item='1',
timestamp=964982703.0, rating=4.0)`.

## Verdict

Both splits ran against the identical cleaned interaction set. The time split
leaks 0 of 1,223 eligible test rows by construction; the random split leaks
17,885 of 18,055 (99.1%). The popularity floor itself moves between the two
(0.0389 vs 0.0496 hit-rate@20), which is the concrete cost of measuring a
downstream model against a leaking split.
