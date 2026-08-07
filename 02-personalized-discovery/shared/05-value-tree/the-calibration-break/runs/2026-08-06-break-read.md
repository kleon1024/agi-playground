# Run — the calibration break that moved the strategy, read from the record

**Date:** 2026-08-06
**Command:** `uv run python core/break_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the weight sweep was the stage's recorded run).

## Purpose

Stage 05's run holds the sharpest result: with weights unchanged and click
predictions inflated 1.6x, the honest and miscalibrated rankings disagree.
This run reads the record and lays out the break and the auction.

## Output

```
  honest ranking:        ['item_10', 'item_11', 'item_8', ...]
  miscalibrated ranking: ['item_11', 'item_10', 'item_6', ...]
  ad auction:
    0.2: ad utility 0.154, does not clear the bar
    0.5: ad utility 0.385, does not clear the bar
    0.8: ad enters, displaces item_6 (organic value 0.499)
```

## Notes

- The same strategy, different calibration, different slate: a
  miscalibrated probability is a different product decision, which is why
  stage 04's ECE is a gate.
- The ad auction at trade_rate 0.8 is the strategy written as arithmetic:
  the ad enters only when its utility clears the organic bar.
