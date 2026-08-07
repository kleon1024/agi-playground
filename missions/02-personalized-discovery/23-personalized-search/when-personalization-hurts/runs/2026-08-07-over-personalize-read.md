# Run — when personalization hurts, executed on the coverage-loss model

**Date:** 2026-08-07
**Command:** `uv run python core/over_personalize.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 23 personalizes search. This run reads the coverage loss when the
history is narrower than the query's intent.

## Output

```
over-personalization, read:
  history:                   ['running shoes reviews', 'trail running']
  broad result for 'shoes': ['running shoes', 'dress shoes', 'hiking boots', 'slippers']
  personalized:              ['trail runners', 'running shoes', 'trail shoes', 'trail boots']

reading: the history pushes the result set toward trail running,
shrinking coverage from four categories to one. When the user's
intent is broader than their history, personalization hides
relevant results — the query's own signal has to win sometimes.
```

## Notes

- The broad result covers four categories; the personalized result
  narrows to trail running, hiding dress shoes, hiking boots, and
  slippers.
- When the user's intent is broader than their history, the query's own
  signal has to win sometimes — personalization is a prior, not a
  replacement for the query.
