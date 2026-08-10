# Run — pacing under demand variance, executed on the delivery simulation

**Date:** 2026-08-06
**Command:** `uv run python core/variance_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Real delivery is uncertain — the morning spike is not known in advance.
This run executes the pacing controller against unexpected demand.

## Output

```
pacing under demand variance, read (cap = budget/hours = 12.5):
  hour  demand  spend  remaining
     0      30   12.5       87.5
     1      28   12.5       75.0
     2      25   12.5       62.5
     3      20   12.5       50.0
     4      15   12.5       37.5
     5      10   10.0       27.5
     6       5    5.0       22.5
     7       2    2.0       20.5
  total spent 79.5 of 100.0
```

## Notes

- Demand exceeds the budget at every early hour and the cap binds — spend
  is flat while demand spikes, and the budget survives the day.
- Without the cap, naive spend would have exhausted the budget in the
  first two hours.
