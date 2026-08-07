# Run — the stale model, executed on the shifting distribution

**Date:** 2026-08-07
**Command:** `uv run python core/stale_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 04's fine-rank model trains on logged interactions. This run freezes
the model's score order at day 0 and moves the true grades, reading the
NDCG decay of an unrefreshed model.

## Output

```
  day 0: NDCG 1.000
  day 1: NDCG 0.628
  day 2: NDCG 0.505
  day 3: NDCG 0.437
  day 4: NDCG 0.371
```

## Notes

- The model's ranking is a snapshot of the distribution it trained on.
- As the distribution moves, the same score order ranks a worse list —
  freshness is a ranking property, not a deployment nicety.
