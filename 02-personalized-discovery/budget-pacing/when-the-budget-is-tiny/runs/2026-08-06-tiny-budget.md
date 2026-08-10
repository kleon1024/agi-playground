# Run — the tiny budget, executed on the pacing controller

**Date:** 2026-08-06
**Command:** `uv run python core/tiny_budget.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 17 shows pacing saving a 100-unit budget. This run tests the
controller on smaller budgets to find the boundary.

## Output

```
  budget   100: naive dark at hour 3, paced dark at hour 5
  budget    20: naive dark at hour 0, paced dark at hour 7
  budget     8: naive dark at hour 0, paced dark at hour 8
```

## Notes

- Pacing stretches every budget: at 20, naive is gone at hour 0 while
  paced survives the day on a 2.5/hour cap.
- But at 8 the cap is 1/hour — the campaign barely delivers. Pacing
  spreads a budget; it cannot create one. The floor is a sizing problem.
