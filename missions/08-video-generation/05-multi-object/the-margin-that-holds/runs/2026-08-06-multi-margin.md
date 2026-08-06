# Run — the margin that holds at two objects, read from the recorded runs

**Date:** 2026-08-06
**Command:** `uv run python core/multi_margin.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads six committed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded runs).

## Purpose

Stage 05's two-object generation still closes MET. This run reads the
recorded JSONs and lays out the margin-vs-spread arithmetic.

## Output

```
  mean 0.1483, spread 0.0104, baseline 0.2193
  margin 0.0710 = 6.8x the spread
```

## Notes

- Two objects still beat frame-repeat by ~6.8x the seed spread — MET holds.
- The capacity limit (one token per frame, two objects) is the finding,
  not a fail.
