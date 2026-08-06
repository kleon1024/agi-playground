# Run — the misspelled query, executed on the stage's tokenizer

**Date:** 2026-08-06
**Command:** `uv run python core/misspelled_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Query normalization handles case, punctuation, and stopwords, but a
misspelling changes the token itself. This run executes the stage's own
tokenizer over misspelled variants.

## Output

```
  'wireless headphones' -> ['wireless','headphones']  exact-match: True
  'wireless heaphones'  -> ['wireless','heaphones']   exact-match: False
  'wireless hedphones'  -> ['wireless','hedphones']   exact-match: False
  'wirless headphones'  -> ['wirless','headphones']   exact-match: True
```

## Notes

- Normalization fixes case and stopwords but not misspelling —
  'heaphones' never becomes 'headphones'.
- Retrieval must either correct the query or match by edit distance,
  which is why spelling correction sits inside query understanding.
