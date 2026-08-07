# Run — the factorial corners, read from the recorded 2x2 codec run

**Date:** 2026-08-06
**Command:** `uv run python core/corners_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the factorial training was the stage's recorded
2026-08-05 run, ~74 min/seed).

## Purpose

Stage 06 crossed dead-code reset with EMA codebook update. This run reads
the recorded grid and the parity checks.

## Output

```
  seed 0 plain: codes 18/64, entropy 0.4051, eval 0.02712, margin 4.3%
  seed 0 reset+ema: codes 64/64, entropy 0.9332, eval 0.01810, margin 36.1%
  seed 1 plain: codes 63/64, entropy 0.7598, eval 0.01698, margin 38.2%
  seed 1 reset+ema: codes 64/64, entropy 0.8723, eval 0.01679, margin 38.9%
  seed 2 plain: codes 32/64, entropy 0.6436, eval 0.02122, margin 22.7%
  seed 2 reset+ema: codes 62/64, entropy 0.8748, eval 0.02051, margin 25.3%
```

## Notes

- The two published corners (plain, reset-only) reproduce stage 04/05's
  numbers to full float precision, so the two new corners (ema-only,
  reset+ema) are measured against the mission's own baselines.
- The reset events column (38, 12, ... of 40) is what answers the
  mechanism question — reset and EMA each contribute, and the record
  separates them.
