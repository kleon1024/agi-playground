# Run — the short query, executed on the stage's classifier

**Date:** 2026-08-06
**Command:** `uv run python core/short_query.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

A short query is ambiguous by construction. This run executes the stage's
tokenizer over single-word queries.

## Output

```
  'shoes' -> ['shoes'] (single intent, but which?)
  'iphone' -> ['iphone'] (single intent, but which?)
  'flight' -> ['flight'] (single intent, but which?)
  'headphones' -> ['headphones'] (single intent, but which?)
  'fix' -> ['fix'] (single intent, but which?)
```

## Notes

- A one-word query classifies trivially but carries no intent signal —
  'shoes' is navigational, transactional, and informational at once.
- The classifier needs context (previous queries, device, time) or must
  hedge the ranking across intents — the short-query problem.
