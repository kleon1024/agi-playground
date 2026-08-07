# Run — the longer list, executed on the two rankers

**Date:** 2026-08-06
**Command:** `uv run python core/list_length.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 12 compares pointwise and pairwise on eight items. This run extends
the list to sixteen and shows the gap growing.

## Output

```
  pointwise  NDCG 0.5747
  pairwise   NDCG 0.5169
```

## Notes

- With more items the formulations diverge further because pairwise
  learns the comparisons that dominate the list, while pointwise's
  absolute scores have more room to disagree.
