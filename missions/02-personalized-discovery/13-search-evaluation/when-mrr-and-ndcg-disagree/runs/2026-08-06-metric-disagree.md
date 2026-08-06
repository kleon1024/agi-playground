# Run — what MRR cannot see, executed on three rankings

**Date:** 2026-08-06
**Command:** `uv run python core/metric_disagree.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

MRR records only the first relevant hit's position. This run shows three
rankings MRR cannot separate.

## Output

```
  one perfect hit, rest empty     NDCG 1.000  MRR 1.000
  strong hits, mis-ordered        NDCG 0.871  MRR 1.000
  mediocre hits, mis-ordered      NDCG 0.922  MRR 1.000
```

## Notes

- All three score MRR 1.0 because the first hit is at position 1; NDCG
  separates them by how the material below is graded and placed.
- MRR is blind to everything after the first hit — the blind spot is why
  graded, top-weighted metrics exist.
