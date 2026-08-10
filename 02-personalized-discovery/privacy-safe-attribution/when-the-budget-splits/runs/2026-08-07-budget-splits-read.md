# Run — when the budget splits, executed on the epsilon-dilution read

**Date:** 2026-08-07
**Command:** `uv run python core/budget_split.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 40's privacy budget is shared. This run splits a total epsilon of 2.0 across 1, 10, and 100 reports.

## Output

```
privacy budget split, read (total epsilon 2.0):
    1 queries: epsilon 2.000 each, noise scale 0.5
   10 queries: epsilon 0.200 each, noise scale 5.0
  100 queries: epsilon 0.020 each, noise scale 50.0

reading: one report gets epsilon 2.0 and noise scale 0.5;
100 reports get epsilon 0.02 each and noise scale 50. The
privacy budget is a shared resource — every additional report
dilutes the signal of all the others.
```

## Notes

- One report gets epsilon 2.0 and noise scale 0.5; 100 reports get epsilon 0.02 each and noise scale 50.
- The privacy budget is a shared resource — every additional report dilutes the signal of all the others.
