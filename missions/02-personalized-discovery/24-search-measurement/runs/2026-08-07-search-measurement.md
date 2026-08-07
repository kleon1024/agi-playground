# Run — search measurement, executed on the zero-result model

**Date:** 2026-08-07
**Command:** `uv run python core/zero_results.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 24 asks what a zero-result query is worth measuring. This run
sorts four zero-result queries into their causes and reads the rate.

## Output

```
zero-result rate, read:
  3/4 queries return nothing
  zero-result rate: 75.0%

reading: two of the four zeros are catalog gaps (no earbuds,
no misspelled-word correction), one is a vocabulary miss. The
rate is a coverage signal: every zero is a query the index
cannot answer, and the breakdown says which fix each needs.
```

## Notes

- Three of four sample queries return nothing, and the causes differ:
  a missing catalog entry, a misspelling, and a vocabulary mismatch
  each need a different fix.
- The zero-result rate is a coverage signal for the search report,
  next to NDCG and MRR — the when-the-zero-result-rate-matters detour
  prices it.
