# Run — LLM query understanding, executed on the intent-slot parser

**Date:** 2026-08-07
**Command:** `uv run python core/intent_slots.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 37 asks how a raw query becomes structured keys. This run parses three queries into intent and slot dictionaries.

## Output

```
llm query understanding, read (intent + slots):
  'cheap flights to tokyo' -> flight_search {'origin': None, 'dest': 'tokyo', 'max_price': 'cheap'}
  '2 bedroom apartment rent' -> housing_search {'bedrooms': 2, 'type': 'apartment', 'action': 'rent'}
  'how do i return an item' -> support {'topic': 'returns'}

reading: the raw string becomes a structured key space. A
missing slot (origin is None) is a decision point: retrieval
either broadens the query or asks for the slot — the empty-slot
detour shows the cost of guessing.
```

## Notes

- The raw string becomes a structured key space retrieval can serve.
- A missing slot (origin is None) is a decision point: broaden the query or ask for the slot — the empty-slot detour shows the cost of guessing.
