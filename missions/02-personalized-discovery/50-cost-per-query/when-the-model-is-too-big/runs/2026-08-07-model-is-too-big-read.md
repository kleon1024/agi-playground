# Run — when the model is too big, executed on the upgrade comparison

**Date:** 2026-08-07
**Command:** `uv run python core/model_too_big.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.10s.
**Cost:** \$0 (local lane).

## Purpose

Stage 50's detour: doubling the fine-rank model buys quality at a cost.
This run compares the small and large models on NDCG and daily cost.

## Output

```
model too big, read (fine-rank cost per query, 10M queries/day):
  small 1.0 units/query, ndcg 0.618, daily 10,000,000 units
  large 2.0 units/query, ndcg 0.631, daily 20,000,000 units

reading: the large model adds 0.013 ndcg and doubles the
daily cost of the fine-rank stage. Whether that is worth it
is a budget question: the same units could buy recall depth,
a cache, or a second experiment. Model size is a cost line,
and cost per query is the unit it is measured in.
```

## Notes

- The large model adds 0.013 NDCG (0.618 to 0.631) and doubles the daily cost from 10M to 20M units.
- Model size is a cost line, and cost per query is the unit it is measured in.
