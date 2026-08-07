# Run — the margin-vs-spread arithmetic, read from the recorded report

**Date:** 2026-08-06
**Command:** `uv run python core/margin_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded outcome report).
**Cost:** \$0 (local lane).

## Purpose

Stage 02's report judged GRPO against both baselines. This run reads the
recorded outcome and lays out the margin-vs-spread comparison.

## Output

```
  greedy decode vs random: margin -0.1493 vs spread 0.0160 -> decisively loses
  greedy decode vs greedy baseline: margin -0.7513 vs spread 0.0160 -> decisively loses
  VERDICT: NOT MET
```

## Notes

- The verdict is honest because the margin is compared against the
  policy's own seed spread — a margin inside the spread is a no-result,
  not a win.
- The policy emitted the same fixed action string on every board in 3/3
  seeds, which is the mechanism behind the decisive losses.
