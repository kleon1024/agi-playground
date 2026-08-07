# Run — when the slot is empty, executed on the broaden-versus-match read

**Date:** 2026-08-07
**Command:** `uv run python core/empty_slot.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 37 parses slots. This run compares retrieval with a missing origin slot against a filled one.

## Output

```
empty slot, read:
  'flights to tokyo': {'origin': None, 'dest': 'tokyo'} -> broaden to all origins
  'flights from sin to tokyo': {'origin': 'sin', 'dest': 'tokyo'} -> exact match

reading: with origin missing, retrieval broadens to every
origin — more coverage, less precision. With the slot filled,
the index answers exactly. The empty slot is a decision: ask,
broaden, or guess, and each has a measured cost.
```

## Notes

- With origin missing, retrieval broadens to every origin — more coverage, less precision; with the slot filled, the index answers exactly.
- The empty slot is a decision: ask, broaden, or guess, and each has a measured cost.
