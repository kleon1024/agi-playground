# Run — marketplace economics, executed on the take-rate revenue model

**Date:** 2026-08-07
**Command:** `uv run python core/take_rate.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 42 asks where the platform's cut stops paying. This run sweeps the take rate and reads revenue.

## Output

```
take rate, read (revenue = take_rate x volume):
  rate 5%: volume 920, revenue $46
  rate 15%: volume 760, revenue $114
  rate 25%: volume 600, revenue $150
  rate 35%: volume 440, revenue $154
  rate 45%: volume 280, revenue $126

reading: raising the take rate raises revenue per transaction
but shrinks volume — revenue peaks at 35% here and falls after.
The platform's cut is a marketplace decision, not a margin
calculation: too high, and the marketplace dies; the same
trade governs ad load (the detour) and the reserve (stage 28).
```

## Notes

- Raising the take rate raises revenue per transaction but shrinks volume — revenue peaks at 35% here and falls after.
- The platform's cut is a marketplace decision, not a margin calculation: too high, and the marketplace dies.
