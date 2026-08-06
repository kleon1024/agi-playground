# Run — the revived codebook, read from the recorded video-codec run

**Date:** 2026-08-06
**Command:** `uv run python core/revive_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-07-31
run).

## Purpose

Stage 01's first three attempts collapsed; the final run revived dead
codes. This run reads the JSON and lays out the final codebook health.

## Output

```
  eval MSE 0.07875 vs background 0.09437 / mean-frame 0.08580
  codes used 63/64, entropy ratio 0.912
  dead codes revived: 158 (revive every 20 steps)
```

## Notes

- Three collapse attempts preceded this: codebook collapse (1/64 codes),
  then the decoder saturation bug.
- The revive mechanism is what kept the codebook at 63/64 while training
  stabilized.
