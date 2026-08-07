# Run — when the user history helps, executed on the prior model

**Date:** 2026-08-07
**Command:** `uv run python core/history_helps.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 23 personalizes search. This run reads how a phone-heavy history
disambiguates an ambiguous query.

## Output

```
history helps, read:
  query 'apple', history ['iphone battery', 'iphone cases']
  apple store support: 0.9
  fruit recipes: 0.4
  apple pie recipe: 0.3

reading: 'apple' alone could be fruit or phone; the phone-heavy
history lifts the support intent. History is a prior over the
query's meaning, and the prior is what personalization adds.
```

## Notes

- The same query means fruit or phone; the phone-heavy history lifts
  the support intent to 0.9 against 0.4 and 0.3.
- History is a prior over the query's meaning, which is exactly what
  personalization adds — and what it risks overriding.
