# Run — the cheap cut's surface rate across keep sizes and scorers

**Date:** 2026-08-06
**Command:** `uv run python core/surface_sweep.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; reuses the stage's `pre_rank.py`
unmodified.
**Wall-clock:** 0.2s.
**Cost:** \$0 (local lane).

## Purpose

Stage 03's pre-rank exists because the fine-ranker is too expensive to run
on the full catalogue. This run measures the cheap proxy's surface rate at
each keep size, against the popularity-only scorer and the fine-rank
ceiling, on the stage's synthetic catalogue.

## Output

```
catalogue 400, true top-20, keep sizes 50/100/200/300
 keep scorer              surface  long-tail  rank rho
   50 cheap_proxy           0.550      0.111     0.293
   50 popularity_only       0.350      0.000     0.366
   50 fine_rank (ceiling)    1.000      1.000     1.000
  100 cheap_proxy           0.850      0.667     0.259
  100 popularity_only       0.500      0.000     0.315
  200 cheap_proxy           1.000      1.000     0.471
  200 popularity_only       0.550      0.000     0.521
```

## Notes

- The cheap proxy needs keep >= 200 to surface all of the true top-20 on
  this catalogue (surface 1.000); at keep 50 it surfaces 55% overall and
  only 11% of the long-tail true-top items.
- popularity_only is structurally long-tail-blind: its long-tail surface
  rate is 0.000 at every keep size. Popularity can never recover an item
  with no history, which is why pre-rank must be a real proxy (content or
  embedding), not a popularity sort — the stage's claim, measured.
- The fine-rank ceiling is 1.000 everywhere; the cheap cut's cost is the
  gap between it and the proxy at small keep sizes.
