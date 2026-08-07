# Run — when the incrementality is zero, executed on the null-result model

**Date:** 2026-08-07
**Command:** `uv run python core/zero_lift.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 30 measures ads by incrementality. This run reads the case where
exposed and control convert at the same rate.

## Output

```
zero incrementality, read:
  exposed 0.030 vs control 0.030
  lift +0.0%

reading: the campaign delivered millions of impressions and
changed nothing — every click it got would have happened without
it. Zero lift is the null result measurement exists to find; a
report that hides it is crediting spend with no effect.
```

## Notes

- Exposed and control both convert at 0.030, so the lift is exactly
  zero — the campaign changed nothing.
- Zero lift is the null result measurement exists to find; a report
  that hides it credits spend with no effect.
