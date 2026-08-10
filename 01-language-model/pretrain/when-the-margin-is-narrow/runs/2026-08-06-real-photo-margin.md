# Run — the real-photo margin, read from the recorded seeds

**Date:** 2026-08-06
**Command:** `uv run python core/real_photo_margin.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded results).
**Cost:** \$0 (local lane; the underlying training was the stage's recorded
run).

## Purpose

Stage 04 compared vision vs text-only on real photographs. This run reads
the recorded seeds and lays out the three numbers the verdict depends on:
the margin, vision's spread, and text-only's spread.

## Output

```
vision:    mean 0.2374 spread 0.0051 per-seed [0.2374, 0.2424, 0.2323]
text-only: mean 0.2222 spread 0.0354 per-seed [0.2121, 0.1919, 0.2626]
margin: +0.0152 — beyond vision's spread (0.0051)? True
text-only spread is 7.0x vision's
```

## Notes

- The margin (+0.0152) is beyond vision's own seed spread (0.0051), so by
  the mission's rule it is a real margin — but it is narrow, far below the
  synthetic set's +0.1105.
- The noise lives on the control side: text-only's spread (0.0354) is 7x
  vision's. The comparison is not "two equally noisy arms"; the vision arm
  is the stable one and the text-only baseline is where the variance is.
