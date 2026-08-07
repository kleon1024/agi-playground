# Run — the split that leaks, read from the recorded MovieLens run

**Date:** 2026-08-06
**Command:** `uv run python core/split_leak.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the underlying split was the stage's recorded
MovieLens run).

## Purpose

Stage 00's recorded run showed the leak as two counts and the popularity
floor as two numbers. This run reads that record and lays out what the 99.1%
leak actually does to the baseline every later stage must beat.

## Output

```
the recorded MovieLens split, read:
  time split:   0/1223 test rows leak the future
  random split: 17885/18055 test rows leak the future (99.1%)
  popularity hit-rate@20: time 0.0389  random 0.0496
  concrete leak: user 75's test row is timestamped

reading: the leak is not a small corruption — it moves the
baseline itself, so comparing scores across splits compares
different experiments.
```

## Notes

- The leak is not a rounding error: 99.1% of random-split test rows have a
  same-user train row after them in time, vs 0 by construction under the
  time split.
- The popularity floor moves between splits (0.0389 vs 0.0496): the baseline
  itself is a function of the split, so a score measured on one split cannot
  be compared with a score measured on the other.
