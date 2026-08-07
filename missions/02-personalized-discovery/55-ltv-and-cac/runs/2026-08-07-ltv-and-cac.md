# Run — LTV and CAC, executed on the unit-economics read

**Date:** 2026-08-07
**Command:** `uv run python core/unit_economics.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 55 introduces unit economics. This run computes the five-month
lifetime value per user for two acquisition channels.

## Output

```
ltv and cac, read (5-month lifetime value per user):
  organic search  cac $2.00, ltv $12.15, ltv/cac 6.08
  paid installs   cac $8.00, ltv $7.50, ltv/cac 0.94

reading: organic search pays back ~6x its acquisition cost;
paid installs return less than the cost of the user - every
paid signup loses money once retention is counted. A channel
with a low CAC is not a cheap channel if its users leave.
Unit economics decide which growth is real growth.
```

## Notes

- Organic search returns 6.08x its CAC; paid installs return 0.94x and lose money once retention is counted.
- A channel with a low CAC is not a cheap channel if its users leave; unit economics decide which growth is real growth.
