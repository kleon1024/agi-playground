# Run — cost per query, executed on the cascade arithmetic

**Date:** 2026-08-07
**Commands:** `uv run python core/cost.py --emit-log /tmp/cost-envelope.json`;
`uv run python prod/cost_audit.py /tmp/cost-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 50 introduces cost per query. This run prices each funnel stage in
cost units, compares the cascade against exhaustive scoring, and prices
the cascade at three catalogue sizes for the audit.

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

scale view (the flat 1.0-each design at catalogue sizes):
  catalogue 10M:
    recall (ann)   1.00 units (25%)
    pre-rank     1.00 units (25%)
    fine-rank    1.00 units (25%)
    mixing       1.00 units (25%)
    total   4.00 units
  catalogue 100M:
    recall (ann)   2.51 units (46%)
    pre-rank     1.00 units (18%)
    fine-rank    1.00 units (18%)
    mixing       1.00 units (18%)
    total   5.51 units
  catalogue  1B:
    recall (ann)   6.31 units (68%)
    pre-rank     1.00 units (11%)
    fine-rank    1.00 units (11%)
    mixing       1.00 units (11%)
    total   9.31 units
```

## Notes

- The cascade costs 4.0 units per query against 200,000 for exhaustive scoring of 10M items.
- Every stage exists to buy the next one a smaller problem; cost per query is the budget capacity planning spends.
- The scale view shows the flat 1.0-each design is a property of the
  10M catalogue: recall's share of the query budget grows from 25% to
  68% as the catalogue reaches 1B, because recall candidates scale
  sublinearly while the later stages hold fixed budgets.
