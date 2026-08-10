# Run — the intent that misroutes, read

**Date:** 2026-08-07
**Command:** `uv run python core/misroute_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Measure what the stage-10 path decision costs when the keyword
classifier misroutes: a collision query (two intent keywords fired) or a
no-signal query (default fallback) picks a retrieval path whose
candidate set is the wrong type, before any ranker runs.

## Output

```
intent misroute, read (NDCG@3 of the routed candidate set):
  buy nike running shoes            transactional -> 1.0000  correct route
  how to fix sleep schedule         informational -> 1.0000  correct route
  best wireless headphones 2026     navigational  -> 1.0000  correct route
  cheap how to fix iphone screen    transactional -> 0.3333  MISROUTED (oracle informational)
  how to buy iphone                 transactional -> 0.3333  MISROUTED (oracle informational)
  redmi note 13 price vs poco x6    transactional -> 0.3333  MISROUTED (oracle informational)
  nike or adidas                    navigational  -> 0.3333  MISROUTED (oracle informational)

  4 of 7 queries misrouted; every misroute
  is a collision (two keywords fired) or a no-signal fallback.

reading: the path decision happens before retrieval. When the
candidate set is the wrong type, the ranker downstream can only
re-order what it was handed. The fix is dual-path retrieval that
carries both candidate types and lets ranking decide, at the
cost of more candidates per query.
```

## Notes

- NDCG@3 is measured against a fixed ideal: the oracle path's top three
  docs at the primary grade. A wrong path carrying only adjacent-grade
  (1) docs scores 0.3333 and cannot normalize itself to 1.0 by being
  uniformly weak.
- The three clean queries route identically under classifier and oracle;
  the four misroutes are exactly the collision and no-signal cases the
  stage-10 audit counts, which is why the audit verdict names the
  failure before the detour measures its cost.
- The oracle intents are declared per query (illustrative); the graded
  relevance gives the adjacent type a partial credit of 1, so a
  misrouted path still earns something when its docs are tolerable but
  not what the user asked for.
