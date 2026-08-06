# Run — the eligibility cascade, read from the recorded MovieLens run

**Date:** 2026-08-06
**Command:** `uv run python core/cascade_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the split was the stage's recorded run).

## Purpose

Stage 00's filter drops rows iteratively. This run reads the record and
lays out what the loop removed and which users the cascade caught.

## Output

```
rows dropped by the iterative filter: 10562
sparse movies (fewer than 5 ratings): 6074 of 9724
users the cascade caught:
  user 175: 24 -> 12
  user 598: 21 -> 16
  user 578: 27 -> 17
```

## Notes

- 10,562 rows dropped, all for item sparsity (6,074 of 9,724 movies have
  under 5 ratings) — eligibility is per item AND per user.
- 8 users fell below the floor after their sparse items were removed: the
  cascade is why the filter loops instead of passing once.
