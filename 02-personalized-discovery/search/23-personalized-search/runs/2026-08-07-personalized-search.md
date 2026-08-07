# Run — personalized search, executed on the user-context model

**Date:** 2026-08-07
**Command:** `uv run python core/user_context.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 23 asks what user context does to a search ranking. This run
scores one query against the same three documents for two users with
different affinity vectors and reads the two orders.

## Output

```
personalized search, read (query 'running shoes', score = relevance + affinity):
  user A: ['trail runners', 'road trainers', 'track spikes']
  user B: ['track spikes', 'road trainers', 'trail runners']

reading: the same query, two orders — user A gets trail runners
first, user B gets track spikes. Personalization is context
added to the query; the risk is that the context overrides the
query's actual intent.
```

## Notes

- The query and relevance scores are identical; only the affinity
  vector differs, and the order flips for the top slot.
- The risk is the context overriding the query — which is what the
  when-personalization-hurts detour measures.
