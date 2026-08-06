# Run — when the slot is scarce, executed on the displacement model

**Date:** 2026-08-06
**Command:** `uv run python core/scarcity_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Displacement depends on slate length. This run sweeps the slate and shows
the curve.

## Output

```
  slots  1 ad displaces  share of slate
      4            0.60         20.0%
      6            0.40         10.3%
      8            0.20          4.5%
```

## Notes

- The same ad displaces 0.60 of value in a 4-slot slate but only 0.20 in
  an 8-slot one — scarcity amplifies the externality.
- Slot count is part of the ad decision, which is why the value tree
  prices displacement per slate, not per ad.
