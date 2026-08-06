# Run — the two-of-six yield, read from the recorded task-mining runs

**Date:** 2026-08-06
**Command:** `uv run python core/yield_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads two recorded run markdowns).
**Cost:** \$0 (local lane; the mining was the stage's recorded runs).

## Purpose

Stage 00 mined task sets from two histories. This run reads both records
and lays out the yields side by side.

## Output

```
  private (100 commits): 2 of 4 candidates survived
  public (2423 commits): 2 of 6 candidates survived
```

## Notes

- Both histories produce the same low yield: most commits that look like
  fixes do not survive fail-at-base/pass-at-gold.
- The verification step, not the mining, is what makes a task real.
