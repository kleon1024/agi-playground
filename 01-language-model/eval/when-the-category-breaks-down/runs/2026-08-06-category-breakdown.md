# Run — the synthetic-set verdict's category structure, read

**Date:** 2026-08-06
**Command:** `uv run python core/category_breakdown.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded breakdown JSON).
**Cost:** \$0 (local lane; the underlying runs were the mission's recorded
ones).

## Purpose

Mission 05's report returned NOT MET but recorded a category breakdown.
This run reads it and lays out the shape: where the vision pathway's
separation from text-only concentrates.

## Output

```
category         vision  text-only   margin
column_shape      0.350      0.333   +0.017
presence          0.574      0.514   +0.060
shape_color       0.501      0.272   +0.229
shape_count       0.432      0.422   +0.010
total_count       0.373      0.203   +0.170
```

## Notes

- The vision pathway separates from text-only most where the question
  cannot leak: shape_color +0.229 (the type unanswerable from question
  text alone) and total_count +0.170 — versus +0.017/+0.010 on the
  leak-prone column_shape and shape_count types.
- The aggregate verdict (NOT MET) hides where the pathway's signal is real:
  the category structure is the evidence that the pathway conditions on
  pixels, which is the mission's positive finding inside the negative
  verdict.
