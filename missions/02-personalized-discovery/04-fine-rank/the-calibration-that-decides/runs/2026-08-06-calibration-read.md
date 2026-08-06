# Run — the calibration that decides, read from the recorded fine-rank run

**Date:** 2026-08-06
**Command:** `uv run python core/calibration_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the fine-rank run was the stage's recorded).

## Purpose

Stage 04 measured negative transfer and click-head calibration at two trunk
sizes. This run reads the record and lays out both panels.

## Output

```
trunk hidden=8 epochs=25:
  click 0.807/0.825, completion 0.750/0.784, satisfaction 0.651/0.706,
  dwell 0.658/0.803 (naive/balanced)
  ECE 0.0722 -> 0.0552 (Platt)
trunk hidden=16 epochs=60:
  click 0.773/0.828, completion 0.721/0.785, satisfaction 0.644/0.664,
  dwell -0.080/0.809
  ECE 0.0956 -> 0.0555 (Platt)
```

## Notes

- Balanced weighting recovers dwell (0.658/-0.080 -> 0.803/0.809): the
  negative-transfer half of the story.
- Platt scaling cuts ECE ~25-40% on the click head; the value tree
  downstream does arithmetic on these probabilities, which is why
  calibration is a gate, not a polish step.
