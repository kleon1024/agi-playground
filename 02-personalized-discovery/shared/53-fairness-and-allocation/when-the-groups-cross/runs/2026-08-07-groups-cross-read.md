# Run — when the groups cross, executed on the definition-flip read

**Date:** 2026-08-07
**Command:** `uv run python core/groups_cross.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 53's detour: the fairness verdict is a function of the group
definition. This run measures the tail category's exposure under a 10%
floor across the catalogue and by segment, and reads the flip.

## Output

```
groups cross, read (tail-category exposure, 10% floor):
  definition          tail exposure  vs floor
  mobile                         8%       -2%
  desktop                       15%       +5%
  catalogue-wide              10.1%     +0.1%

reading: across the whole catalogue the tail clears the
floor (10.1% vs 10%), so the allocation looks fair. Split the
same allocation by segment and the mobile segment - 70% of
traffic - leaves the tail at 8%, below the floor. The verdict
flips with the definition: group choice is a policy decision,
and the fair-looking aggregate hides the majority segment that
is below the bar. Define the group before measuring fairness,
and report both views, not the one that clears the bar.
```

## Notes

- The catalogue-wide tail exposure (10.1%) clears the 10% floor, but the
  mobile segment — 70% of traffic — leaves the tail at 8%, below it; the
  verdict flips with the definition.
- Exposure bias is multi-sided: the serving surface, the segment, and
  the catalogue each produce a different exposure statement
  (Abdollahpouri et al., KDD Workshop 2020), and group definitions carry
  assumptions (Ekstrand et al., FAT* 2018). The fix is to name the group
  before measuring fairness and report both views.
