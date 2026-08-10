# Run — when the feature diverges, executed on the train-versus-serve read

**Date:** 2026-08-07
**Command:** `uv run python core/feature_diverges.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 43's store exists because the naive path diverges. This run reads
the divergence directly: the same items scored with the training-time
feature and the serve-time feature.

## Output

```
feature diverges, read (score at train hour 0 vs serve hour 5):
  P1001: train score 17.5, serve score 12.5
  P1002: train score 17.5, serve score 17.5
  P1003: train score 11.5, serve score 7.5
  train order: ['P1001', 'P1002', 'P1003']
  serve order: ['P1002', 'P1001', 'P1003']

reading: the items are the same; only the feature differs.
The training-time ranker sees every item as new and puts
P1001 first; at serve time P1002 is the fresh one and wins
on an age feature the model never trained on. The divergence
is not a model bug - it is the two reads disagreeing about
the world, which is what the store prevents.
```

## Notes

- Training order puts P1001 first; serve order puts P1002 first, on an age feature the model never trained on.
- The divergence is not a model bug — the two reads disagree about the world, which is what the store prevents.
