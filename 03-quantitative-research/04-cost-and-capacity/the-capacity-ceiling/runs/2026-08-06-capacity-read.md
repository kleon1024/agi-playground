# Run — the capacity ceiling, read from the recorded cost-and-capacity run

**Date:** 2026-08-06
**Command:** `uv run python core/capacity_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the cost-and-capacity run was the stage's
recorded).

## Purpose

Stage 04 measured ADV and volatility, then priced a 10m book against
assumed costs. This run reads the record and lays out where the book stops.

## Output

```
  ADV USD 12,578,055,538
  daily volatility 1.7839%
  at a USD 10m book, 0.0398% participation and 0.2780% annual cost
  discrete-sweep peak USD 25,156,111,076
  total-return breakeven USD 125,780,555,379
```

## Notes

- Participation caps the book by liquidity (the discrete-sweep peak);
  breakeven caps it by cost (the total-return ceiling).
- ADV and volatility are measured; all costs and return assumptions are
  declared, not fitted execution evidence.
