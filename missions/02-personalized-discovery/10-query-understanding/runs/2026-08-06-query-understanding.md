# Run — query understanding, executed on the stage's own pipeline

**Date:** 2026-08-06
**Command:** `uv run python core/query_understanding.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Search begins with the query, and the query is a string with noise. This
run executes the stage's tokenize-normalize-classify pipeline over six
realistic queries and measures what each step does.

## Output

```
  'best wireless headphones 2026' -> ['best','wireless','headphones','2026'] -> navigational
  'buy iPhone 17 Pro Singapore'   -> ['buy','iphone','17','pro','singapore'] -> transactional
  'how to fix sleep schedule'     -> ['how','fix','sleep','schedule'] -> informational
  'Nike Air Max size 9'           -> ['nike','air','max','size','9'] -> navigational
  'cheap flights SIN to NRT'      -> ['cheap','flights','sin','nrt'] -> transactional
  'redmi note 13 vs poco x6'      -> ['redmi','note','13','vs','poco','x6'] -> informational
  vocabulary across 6 queries: 28 terms
```

## Notes

- Normalization removes the noise that would split the index (the/A/The
  map to one key); stopwords drop from the query before retrieval.
- Intent classification decides the retrieval path: navigational needs
  exact match, transactional needs price, informational needs coverage.
