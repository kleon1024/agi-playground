# Run — advertiser ROAS, executed on the weekly lifecycle model

**Date:** 2026-08-07
**Command:** `uv run python core/roas.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 54 introduces advertiser economics. This run tracks one
advertiser's spend, conversions, and ROAS over four weeks.

## Output

```
advertiser roas, read (spend $1000/week, aov $28):
  week 1: spend $1000, conversions 310, revenue $8680, roas 8.68
  week 2: spend $1000, conversions 325, revenue $9100, roas 9.10
  week 3: spend $1000, conversions 265, revenue $7420, roas 7.42
  week 4: spend $1000, conversions 165, revenue $4620, roas 4.62

reading: roas falls from a strong start to 4.62, below the target of 5.0.
The advertiser does not leave at a plateau; they leave when
the marginal dollar stops paying. The platform that watches
only its own revenue is watching the advertiser walk away.
```

## Notes

- ROAS falls from 9.10 in week 2 to 4.62 in week 4, below the target of 5.0.
- The advertiser does not leave at a plateau; they leave when the marginal dollar stops paying.
