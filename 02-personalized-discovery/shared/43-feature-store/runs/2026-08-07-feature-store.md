# Run — feature store, executed on the read-at-serve-time model

**Date:** 2026-08-07
**Command:** `uv run python core/feature_store.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.10s.
**Cost:** \$0 (local lane).

## Purpose

Stage 43 introduces the feature store. This run reads the same items at
serve time through the store and through a naive recompute, and compares
the scores the ranker would see.

## Output

```
feature store, read at serve time (hour 5):
  P1001: price $49.00, age 0h, ctr 0.032, score 17.5
  P1002: price $89.00, age 0h, ctr 0.032, score -2.5
  P1003: price $19.00, age 0h, ctr 0.011, score 11.5

naive recompute at serve time (hour 5):
  P1001: price $49.00, age 5h, ctr 0.032, score 12.5
  P1002: price $89.00, age 3h, ctr 0.032, score -5.5
  P1003: price $19.00, age 4h, ctr 0.011, score 7.5

reading: the store serves age 0.0 to training and serving
alike; the naive path serves age 3-5 at serve time. The ranker
reorders on a feature the model never saw - equality of the
two reads is the whole point of the store.
```

## Notes

- The store serves age 0.0 to training and serving alike; the naive path serves age 3-5 at serve time.
- The ranker reorders on a feature the model never saw — equality of the two reads is the whole point of the store.
