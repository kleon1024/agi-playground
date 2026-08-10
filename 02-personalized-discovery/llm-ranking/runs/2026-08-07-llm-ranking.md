# Run — LLM listwise ranking, executed on the reorder model

**Date:** 2026-08-07
**Command:** `uv run python core/llm_rank.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.12s.
**Cost:** \$0 (local lane).

## Purpose

Stage 31 asks what an LLM ranker does to a candidate list. This run compares the pointwise order with the listwise reorder and reads the positions the LLM changes.

## Output

```
llm listwise ranking, read:
  pointwise: ['d1', 'd2', 'd3', 'd4', 'd5']
  listwise:  ['d4', 'd2', 'd5', 'd1', 'd3']
  positions changed: 4/5

reading: the LLM sees the list as context and reorders it —
d4 jumps to the top because the instruction reading favors it.
The frontier cost is latency and prompt length, which is why
LLM ranking sits at the top of a cascade, not over the whole
candidate set.
```

## Notes

- The LLM reorders 4 of 5 positions; d4 jumps to the top because the instruction reading favors it.
- The frontier cost is latency and prompt length, which is why LLM ranking sits at the top of a cascade, not over the whole candidate set.
