# Run — fairness and allocation, executed on the exposure-budget read

**Date:** 2026-08-07
**Command:** `uv run python core/allocation.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 53 introduces allocation. This run measures exposure by category
with and without a 10% per-category floor.

## Output

```
fairness and allocation, read (exposure by category):
  unconstrained:
    audio        ctr 0.040 exposure 59%
    video        ctr 0.032 exposure 30%
    cable        ctr 0.022 exposure 10%
    accessories  ctr 0.010 exposure 1%
    aggregate ctr: 0.0355
  with a 10% per-category floor:
    audio        ctr 0.040 exposure 54%
    video        ctr 0.032 exposure 28%
    cable        ctr 0.022 exposure 9%
    accessories  ctr 0.010 exposure 9%
    aggregate ctr: 0.0334

reading: the floor moves accessories from near-invisible to
a real share and costs a little aggregate ctr. Allocation is
a constraint on the ranking objective, and the price of the
constraint is measured, not assumed.
```

## Notes

- The 10% floor moves accessories from 1% to 9% of exposure at a cost of 0.0021 aggregate CTR (0.0355 to 0.0334).
- Allocation is a constraint on the ranking objective, and the price of the constraint is measured, not assumed.
