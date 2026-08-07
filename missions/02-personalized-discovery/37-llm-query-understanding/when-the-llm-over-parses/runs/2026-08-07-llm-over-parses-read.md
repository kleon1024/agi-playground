# Run — when the LLM over-parses, executed on the invented-slot read

**Date:** 2026-08-07
**Command:** `uv run python core/over_parse.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 37's parser can invent constraints. This run compares an over-parsed query with an honest parse.

## Output

```
over-parse, read:
  query: 'flights to tokyo'
  over-parsed: {'dest': 'tokyo', 'max_price': 'cheap'}  (max_price invented)
  honest:      {'dest': 'tokyo', 'max_price': None}  (max_price absent)

reading: the over-parsed version invents 'cheap' and would
filter the index by a constraint the user never stated. LLM
parsing needs a confidence floor per slot — an invented slot
silently shrinks recall exactly like an over-eager rule.
```

## Notes

- The over-parsed version invents 'cheap' and would filter the index by a constraint the user never stated.
- LLM parsing needs a confidence floor per slot — an invented slot silently shrinks recall exactly like an over-eager rule.
