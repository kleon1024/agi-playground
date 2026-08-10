# Run — the correction, executed on the miscalibrated estimate

**Date:** 2026-08-06
**Command:** `uv run python core/correction_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 16 measures ECE, but the fix is a correction. This run applies a
multiplicative correction and shows the ECE drop.

## Output

```
  mean predicted 0.545, observed 0.300
  correction factor 0.550
  ECE before 0.2450 -> after 0.0000
```

## Notes

- A single multiplicative correction — scale predictions by
  observed/predicted — removes the systematic bias.
- The before/after is the measure of what calibration exists to do.
