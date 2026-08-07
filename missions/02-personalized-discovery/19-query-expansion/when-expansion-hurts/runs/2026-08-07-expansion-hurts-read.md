# Run — when expansion hurts, executed on the ambiguity model

**Date:** 2026-08-07
**Command:** `uv run python core/expansion_hurts.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 19 expands a query. This run shows the precision price: what the
expanded query adds to the result set when the term is ambiguous.

## Output

```
expansion hurts, read:
  base query 'apple': 4 hits — all relevant
  expanded: 4 hits — including wrong senses
  new hits from expansion: []

reading: expansion trades precision for recall. The phone and
laptop docs join the result set because 'apple' means phone in
one context and fruit in another — the ambiguity is the cost.
```

## Notes

- The base query's four hits are all relevant; the expanded query still
  returns four, but now includes the wrong senses.
- Expansion added no new relevant hits here — the ambiguity is the
  cost, and expansion needs a sense signal to pay for it.
