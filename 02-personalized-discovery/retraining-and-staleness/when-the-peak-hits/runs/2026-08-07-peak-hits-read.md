# Run — when the peak hits, executed on the retraining-cadence read

**Date:** 2026-08-07
**Command:** `uv run python core/peak_hits.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 46's detour: retraining cadence is a resource decision, and the
when matters as much as the count. This run compares a calendar
cadence (retrain every 12 hours) against an error trigger (retrain the
first hour the measured rank error crosses its budget) through a demand
spike at hours 8-12.

## Output

```
peak hits, read (spike hours 8-12, retrain when >1 pair wrong):
  hour  calendar  adaptive
    0       0         0 R R
    1       0         0
    2       0         0
    3       0         0
    4       0         0
    5       0         0
    6       0         0
    7       0         0
    8       2         2   R
    9       2         0
   10       2         0
   11       2         0
   12       0         0 R
   13       2         2   R
   14       2         0

  retrains:     calendar 2, adaptive 3
  error-hours:  calendar 12, adaptive 4
  peak error:   calendar 2, adaptive 2

reading: the calendar retrained at hour 12, mid-spike, so it
served the stale order for every spike hour and again after the
spike ended. The trigger spent one extra retrain on the first
hour each world change became measurable and cut stale exposure
threefold. The retraining decision is the when, not the count -
a fixed cadence spends its budget on the calendar, an error
trigger spends it on the world.
```

## Notes

- The spike at hours 8-12 boosts the volatile cohort, flipping two
  pairwise orderings. The calendar's scheduled hour-12 retrain lands
  mid-spike, so it serves the stale order at hours 8-11 and again at
  13-14 after the world snaps back.
- The error trigger retrains at hour 8 (first measurable hour of the
  spike) and hour 13 (first hour after it ended), holding stale exposure
  to one hour per world change for one extra retrain — 4 error-hours
  against 12.
- The trade is the one Verachtert, Jeunen, and Goethals model in
  "Scheduling on a budget: Avoiding stale recommendations with timely
  updates" (Machine Learning with Applications, 2023): schedule
  retraining to maximize accuracy within a fixed resource budget, with
  the staleness rate derived from the data rather than assumed by a
  calendar.
