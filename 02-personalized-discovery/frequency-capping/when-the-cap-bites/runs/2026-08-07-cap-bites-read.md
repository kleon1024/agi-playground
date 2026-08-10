# Run — when the cap bites, executed on the reach-allocation model

**Date:** 2026-08-07
**Command:** `uv run python core/cap_bites.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 25 caps frequency. This run allocates a fixed impression budget
across cap levels and reads the reach trade.

## Output

```
cap bites, read (10,000-impression budget):
  cap 1: reaches 10,000 users at 1 impressions each
  cap 3: reaches 3,333 users at 3 impressions each
  cap 5: reaches 2,000 users at 5 impressions each
  cap 10: reaches 1,000 users at 10 impressions each

reading: the same budget reaches 10,000 users at cap 1 and only
1,000 at cap 10. A high cap preserves per-user value but shrinks
reach; the campaign's goal decides which side of the trade it
needs. The cap is a budget allocation, not a display setting.
```

## Notes

- The same 10,000-impression budget reaches 10,000 users at cap 1 and
  only 1,000 at cap 10.
- A high cap preserves per-user value but shrinks reach — the cap is a
  budget allocation, and the campaign's goal picks the point on the
  trade.
