# Run — the per-cohort staleness panel over the emitted item table

**Date:** 2026-08-07
**Commands:** `uv run python core/staleness.py --emit-log /tmp/staleness-envelope.json`;
`uv run python prod/staleness_panel.py /tmp/staleness-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 46's staleness grows with snapshot age, but not uniformly. This
run is the case-finding half of the stage: how a team finds which cohort
is aging. The core script emits the item table with cohort tags; the
production panel computes pairwise rank error per cohort for each
snapshot hour evaluated at each later hour.

## Output

```
staleness panel, rank error vs snapshot age per cohort:
  cohort    items  snap0@6  snap0@12  snap6@12
  all           6        5         6         1
  volatile      4        2         2         0
  stable        2        0         0         0

verdict: VOLATILE FIRST -- the volatile cohort out-degrades the
stable one by hour 6, so a retraining trigger tuned to the
aggregate average leaves the fast movers stale longest. The
trigger should follow the measured error per cohort, not a
calendar or the average.
```

## Notes

- The volatile cohort ranks two pairs wrong at hour 6 while the stable
  cohort is still exact; the aggregate row (5 at hour 6) mixes the
  volatile cohort's errors with cross-cohort pairs, which is why a
  single aggregate trigger cannot name which cohort is due.
- The panel is the data-side counterpart of Verachtert, Jeunen, and
  Goethals' result that staleness rate is environment-dependent and
  derivable from the logs (Verachtert et al., "Scheduling on a budget:
  Avoiding stale recommendations with timely updates", Machine Learning
  with Applications, 2023).
