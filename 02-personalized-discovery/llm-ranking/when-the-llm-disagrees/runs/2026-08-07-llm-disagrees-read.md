# Run — when the LLM disagrees, executed on the head-versus-tail disagreement read

**Date:** 2026-08-07
**Command:** `uv run python core/llm_disagrees.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 31 adds an LLM listwise ranker. This run compares the pointwise and listwise orders and reads where the disagreement sits.

## Output

```
llm disagreement, read:
  pointwise: ['d1', 'd2', 'd3', 'd4', 'd5', 'd6']
  listwise:  ['d2', 'd1', 'd3', 'd4', 'd5', 'd6']
  head positions changed: 2/3
  tail positions changed: 0/3

reading: the disagreement concentrates in the head — the LLM
reorders the top of the list where the user actually looks.
When the disagreement is in the tail, the LLM is spending its
latency on positions nobody reaches.
```

## Notes

- The disagreement concentrates in the head: 2/3 head positions change, 0/3 tail positions.
- When the disagreement is in the tail, the LLM is spending its latency on positions nobody reaches.
