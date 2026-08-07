# Run — the dense path, executed on the embedding contrast

**Date:** 2026-08-06
**Command:** `uv run python core/dense_contrast.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 11 shows BM25's synonym failure; the fix is a dense matcher. This
run computes a hand-built embedding contrast to make the mechanism
concrete.

## Output

```
  query vs doc_running_shoes    cosine 0.816
  query vs doc_running_footwear cosine 0.408
  query vs doc_headphones       cosine 0.000
```

## Notes

- doc_running_footwear shares 'running' and its footwear/athletic concepts
  embed near 'shoes', so dense similarity is meaningful where BM25 scored
  low.
- The embedding is the mechanism behind hybrid search's synonym coverage.
