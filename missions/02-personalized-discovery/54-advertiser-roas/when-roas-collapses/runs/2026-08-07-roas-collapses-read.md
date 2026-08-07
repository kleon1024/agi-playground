# Run — when ROAS collapses, executed on the scale-up read

**Date:** 2026-08-07
**Command:** `uv run python core/roas_collapses.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 54's detour: the advertiser raises the budget to buy more
conversions, and each later dollar reaches a colder audience. This run
reads CPA and ROAS as spend scales.

## Output

```
roas collapses, read (aov $28, cpa target $5):
  spend $1000: conversions 310, cpa $3.23, roas 8.68
  spend $2000: conversions 430, cpa $4.65, roas 6.02
  spend $3000: conversions 455, cpa $6.59, roas 4.25

reading: doubling the budget buys only 120 more conversions;
the third thousand buys 25. CPA climbs from $3.23 to $6.59
and ROAS falls below the $5 target. The marginal dollar is
the whole story of scaling - the average return hides that
the next dollar loses money.
```

## Notes

- Doubling spend buys 120 more conversions; the third thousand buys 25, and CPA climbs from \$3.23 to \$6.59.
- The marginal dollar is the whole story of scaling — the average return hides that the next dollar loses money.
