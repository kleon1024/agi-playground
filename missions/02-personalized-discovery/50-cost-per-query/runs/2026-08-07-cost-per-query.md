# Run — cost per query, executed on the cascade arithmetic

**Date:** 2026-08-07
**Command:** `uv run python core/cost.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 50 introduces cost per query. This run prices each funnel stage in
cost units and compares the cascade against exhaustive scoring.

## Output

```
cost per query, read (cost units):
  recall (ann)   100,000 candidates x 0.00001 = 1.0
  pre-rank       1,000 candidates x 0.00100 = 1.0
  fine-rank         50 candidates x 0.02000 = 1.0
  mixing            20 candidates x 0.05000 = 1.0
  total per query: 4.0 units
  exhaustive fine-rank of 10M items: 200000 units
  per 1M queries, cascade: 4,000,000 units
  per 1M queries, exhaustive: 200,000,000,000 units

reading: the cascade costs a fraction of exhaustive scoring,
and every stage exists to buy the next one a smaller problem.
Cost per query is the budget that capacity planning spends.
```

## Notes

- The cascade costs 4.0 units per query against 200,000 for exhaustive scoring of 10M items.
- Every stage exists to buy the next one a smaller problem; cost per query is the budget capacity planning spends.
