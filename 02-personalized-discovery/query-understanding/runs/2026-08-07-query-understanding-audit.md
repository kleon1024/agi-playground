# Run — the intent-mix audit over the emitted query log

**Date:** 2026-08-07
**Command:** `uv run python core/query_understanding.py --emit-log /tmp/query-understanding-envelope.json` then `uv run python prod/intent_audit.py /tmp/query-understanding-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib and pandas 3.0.5.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stratify the stage-10 keyword classifier's intent assignments by head and
tail queries, and count the two silent failures: a query whose keywords
fire two intent classes (assigned by rule order), and a query with no
keyword at all (default fallback to navigational).

## Output

```
intent-mix audit over the query log:
  aggregate intent mix (32 queries):
    navigational    8  25.0%  no-keyword 8  collision 0
    transactional  13  40.6%  no-keyword 0  collision 3
    informational  11  34.4%  no-keyword 0  collision 0

  collisions (two intent classes fired, rule order decided):
    tail  'cheap how to fix iphone screen'           transactional/informational -> transactional
    tail  'how to buy iphone'                        transactional/informational -> transactional
    tail  'redmi note 13 price vs poco x6'           transactional/informational -> transactional

  head vs tail stratification:
    head  12 queries ( 37.5%)  no-keyword 3 (25.0%)  collision 0 ( 0.0%)
    tail  20 queries ( 62.5%)  no-keyword 5 (25.0%)  collision 3 (15.0%)

verdict: INTENT COLLISION -- the aggregate mix says the rule
order is fine, but every collision query is in the tail:
tail carries all 3 collisions
(15% of tail) against 0 of head.
Rule order (transactional before informational) silently
decides the retrieval path for these; the fix is a
confidence-aware intent model with an explicit ambiguous
bucket, or dual-path retrieval that does not force one intent.
```

## Notes

- The audit reads the emitted envelope, not the console print: the core
  writes the same six reads plus the query-log cohort (32 queries, head
  and tail) that the audit stratifies.
- The three collision queries are all tail queries; the rule order
  (transactional before informational) silently picks a retrieval path
  for each. Five of the six no-keyword tail queries want comparison,
  review, or guide content that the navigational fallback cannot route.
- Intent labels in production are click-derived and noisy; Kumar, Hu,
  Headden, Goutam, Lin and Yin, "Shareable Representations for Search
  Query Understanding", arXiv:2001.04345 (2020) build intent
  representations for shopping search while accounting for exactly this
  noisiness and sparseness of query data. The audit stratifies where
  that label noise concentrates: the tail.
