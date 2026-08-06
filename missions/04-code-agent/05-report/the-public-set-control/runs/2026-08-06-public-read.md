# Run — the public-set control, read from the recorded outcome report

**Date:** 2026-08-06
**Command:** `uv run python core/public_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded outcome report).
**Cost:** \$0 (local lane).

## Purpose

Stage 05's bullet-4 finding is that the public set exists and is reported
separately. This run reads the recorded report and lays out the two sets.

## Output

```
  private (harness, stage 03, all tiers pooled for display only): 18/18
  public (harness, haiku only): 6/6
  reported side by side, never averaged into one figure.
```

## Notes

- The public set is the contamination-prone counterpart: its 6/6 says
  nothing about the private 18/18.
- Pooling them would hide which set each number belongs to, which is the
  bullet-4 rule.
