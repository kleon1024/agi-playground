# Run — conversational search, executed on the session-context resolution model

**Date:** 2026-08-07
**Command:** `uv run python core/session_context.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 36 asks how a follow-up query resolves. This run scores candidate intents with and without session context.

## Output

```
conversational search, read:
  turn 1: 'best running shoes for marathons'
  turn 2: 'what about the cheaper ones'
  candidate intents (with context, without):
    cheaper marathon shoes: 0.8 vs 0.2
    cheaper headphones: 0.1 vs 0.6
    cheaper laptops: 0.1 vs 0.2
  resolved: cheaper marathon shoes

reading: without context the follow-up is ambiguous; with the
session it resolves to the cheaper marathon shoes. The query
is only part of the input — the session is the other part.
```

## Notes

- Without context the follow-up is ambiguous; with the session it resolves to the cheaper marathon shoes.
- The query is only part of the input — the session is the other part.
