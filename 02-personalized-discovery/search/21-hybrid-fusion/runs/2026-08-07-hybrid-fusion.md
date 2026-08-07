# Run — hybrid fusion, executed on reciprocal rank fusion

**Date:** 2026-08-07
**Command:** `uv run python core/fuse_sets.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 21 asks how lexical and dense candidate sets become one answer
list. This run executes reciprocal rank fusion over two short lists and
reads which documents rise.

## Output

```
hybrid fusion, read (reciprocal rank fusion):
  d1: 0.0323 (lexical#1, dense#3)
  d4: 0.0320 (lexical#4, dense#1)
  d2: 0.0161 (lexical#2)
  d5: 0.0161 (dense#2)
  d3: 0.0159 (lexical#3)
  d6: 0.0156 (dense#4)

reading: d4 and d1 appear in both sets and rank highest; d2, d3
survive only from lexical; d5, d6 only from dense. Fusion keeps
the union while rewarding documents both matchers agree on.
```

## Notes

- Documents in both sets (d1, d4) score roughly double the survivors,
  because reciprocal rank fusion sums each matcher's rank contribution.
- The union is preserved: d2/d3 from lexical and d5/d6 from dense all
  stay retrievable, which is the recall guarantee stage 21 exists for.
