# Run — when the topic shifts, executed on the stale-context read

**Date:** 2026-08-07
**Command:** `uv run python core/topic_shift.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 36 resolves follow-ups with session context. This run shifts the topic mid-session and reads the stale-context failure.

## Output

```
topic shift, read:
  'running shoes' -> search_marathon
  'what about the cheaper ones' -> search_marathon
  'actually, book a hotel in tokyo' -> search_hotel
  'any good ones near shibuya' -> search_marathon (stale)

reading: the fourth query is about hotels, but the session
context still points at marathon shoes, so 'near shibuya' is
misread. Conversation needs a topic boundary: when the intent
class changes, the old context has to expire.
```

## Notes

- The fourth query is about hotels, but the session context still points at marathon shoes, so 'near shibuya' is misread.
- Conversation needs a topic boundary: when the intent class changes, the old context has to expire.
