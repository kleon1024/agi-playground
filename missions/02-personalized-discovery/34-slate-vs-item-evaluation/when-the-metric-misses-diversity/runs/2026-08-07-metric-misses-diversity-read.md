# Run — when the metric misses diversity, executed on the blind-spot read

**Date:** 2026-08-07
**Command:** `uv run python core/metric_blind.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 34's evaluation metric must see the slate. This run compares two slates on item-score sum and on slate value.

## Output

```
metric blind spot, read:
  slate_a item sum 2.40, slate value 2.88
  slate_b item sum 2.40, slate value 3.84

reading: the item-level metric ties the slates (2.40 = 2.40)
while the slate metric separates them (2.88 vs 3.84). A report
that only averages item scores cannot see the page the user
actually got.
```

## Notes

- The item-level metric ties the slates (2.40 = 2.40) while the slate metric separates them (2.88 vs 3.84).
- A report that only averages item scores cannot see the page the user actually got.
