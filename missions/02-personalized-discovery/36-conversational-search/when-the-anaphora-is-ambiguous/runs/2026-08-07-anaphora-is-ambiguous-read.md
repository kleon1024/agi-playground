# Run — when the anaphora is ambiguous, executed on the referent-tracking read

**Date:** 2026-08-07
**Command:** `uv run python core/anaphora.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 36 must resolve referents. This run reads a two-entity session and the ambiguous follow-up.

## Output

```
anaphora, read:
  entities in session: ['trail runners', 'road trainers']
  follow-up: 'are they waterproof?'
    'they' -> trail runners: plausible
    'they' -> road trainers: ambiguous

reading: 'they' is ambiguous between two shoe types in the
session. Resolving it wrong changes the answer — conversational
search has to track referents, not just reuse the last query.
```

## Notes

- 'they' is ambiguous between two shoe types in the session; resolving it wrong changes the answer.
- Conversational search has to track referents, not just reuse the last query.
