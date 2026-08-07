# Run — when retention flattens, executed on the 24-month LTV projection

**Date:** 2026-08-07
**Command:** `uv run python core/retention_flattens.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 55's detour: two cohorts retain the same share in month one, but one
flattens at a floor. This run projects 24-month LTV for both.

## Output

```
retention flattens, read (24-month ltv per user):
  decaying cohort (floor 0):    ltv $27.54
  flattening cohort (floor 35%): ltv $50.83
  month 12 retention: decaying 1%, flattening 35%

reading: both cohorts decay at the same rate for months;
the floor decides the difference. A 35% floor nearly doubles
LTV because the flat tail compounds over the horizon.
Retention work - which is what good discovery is - changes
the floor, and the floor is worth more than any single
month's revenue.
```

## Notes

- A 35% retention floor nearly doubles 24-month LTV: \$27.54 to \$50.83, with month-12 retention at 35% versus 1%.
- Retention work — which is what good discovery is — changes the floor, and the floor is worth more than any single month's revenue.
