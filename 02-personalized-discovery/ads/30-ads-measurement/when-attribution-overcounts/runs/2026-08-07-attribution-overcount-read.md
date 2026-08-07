# Run — when attribution overcounts, executed on the credit-allocation model

**Date:** 2026-08-07
**Command:** `uv run python core/overcount.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 30 measures ads. This run reads how a last-click model credits a
multi-touch conversion.

## Output

```
attribution, read:
  multi-touch shares: {'search ad': 0.4, 'display ad': 0.2, 'email': 0.4}
  last-click model credits 'email' with 1.0
  overcount: 0.6 of the credit

reading: last-click gives the final touchpoint the whole
conversion, crediting email with 0.6 of value it shared. The
measurement model decides which channel gets the budget — an
overcounting model misallocates spend even when the ads work.
```

## Notes

- The three touchpoints share credit 0.4/0.2/0.4, but last-click gives
  email all 1.0 — an overcount of 0.6.
- The measurement model decides which channel gets the budget, so an
  overcounting model misallocates spend even when the ads work.
