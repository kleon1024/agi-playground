# Run — when the prompt token budget binds, executed on the budget-truncation read

**Date:** 2026-08-07
**Command:** `uv run python core/token_budget.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 31's LLM ranker sees a bounded prompt. This run truncates a five-item list to a four-item budget and reads the consequence.

## Output

```
prompt token budget, read (list of 5, budget 4):
  LLM sees: ['d1', 'd2', 'd3', 'd4']
  truncated: ['d5']
  best truncated score: 0.99

reading: d5 scores 0.99 but sits outside the budget, so the
LLM never sees it and the pointwise order decides its fate.
The prompt budget is the LLM ranker's recall boundary — the
same cutoff question stage 22 asked, with tokens instead of
milliseconds.
```

## Notes

- d5 scores 0.99 but sits outside the budget, so the LLM never sees it and the pointwise order decides its fate.
- The prompt budget is the LLM ranker's recall boundary — the same cutoff question stage 22 asked, with tokens instead of milliseconds.
