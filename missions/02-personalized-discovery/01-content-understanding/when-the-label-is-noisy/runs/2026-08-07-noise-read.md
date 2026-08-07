# Run — label noise, executed on the thresholded classifier

**Date:** 2026-08-07
**Command:** `uv run python core/noise_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 01 classifies content by a confidence threshold. This run labels
items with a noisy oracle and reads what the noise does to the items the
threshold keeps.

## Output

```
  a: true=recipe label=recipe conf=0.91 kept ok
  b: true=recipe label=recipe conf=0.84 kept ok
  c: true=news label=recipe conf=0.78 kept WRONG
  d: true=recipe label=news conf=0.74 kept WRONG
  e: true=news label=news conf=0.62 cut ok

  reading: 2/4 kept items carry a correct label.
```

## Notes

- The threshold gates confidence, not truth — label noise passes through
  it.
- Precision is a property of the label source first, and of the
  threshold second.
