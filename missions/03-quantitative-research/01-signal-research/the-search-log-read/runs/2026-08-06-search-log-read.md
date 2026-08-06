# Run — the search log, read from the recorded signal-search run

**Date:** 2026-08-06
**Command:** `uv run python core/search_log_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the signal search was the stage's recorded run).

## Purpose

Stage 01's run logged every candidate and then permuted forward returns to
price the search. This run reads the record and lays out the two numbers
that decide whether the best signal is real.

## Output

```
  candidates logged: 32
  best in-sample IC: 0.0947 (momentum, 24 month)
  null searches matching the winner: 95/300
  permutation p-value: 0.317
```

## Notes

- The winner is real only if it survives the search itself: 95 of 300 null
  searches matched or exceeded it, so p=0.317 — not a result.
- The search log (32 candidates, disclosed) is what makes the multiple-
  testing correction possible at all.
