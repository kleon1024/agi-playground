# Run — the moving baseline, executed across three periods

**Date:** 2026-08-07
**Command:** `uv run python core/baseline_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 09 reports the mission outcome against a popularity baseline. This
run recomputes the baseline per period and reads the verdict changing as
the baseline drifts.

## Output

```
  w1: system 0.42 vs baseline 0.38 -> beats
  w2: system 0.45 vs baseline 0.46 -> LOSES
  w3: system 0.44 vs baseline 0.39 -> beats
```

## Notes

- The same system beats popularity in week 1, loses in week 2, and wins
  again in week 3.
- The baseline is not a constant, it is the demand curve; a report dated
  to one period says when the win holds, not forever.
