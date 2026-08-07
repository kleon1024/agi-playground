# Run — when the reserve moves revenue, executed on the reserve-sweep model

**Date:** 2026-08-07
**Command:** `uv run python core/reserve_revenue.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 28 studies auction revenue. This run sweeps the reserve price and
reads the fill-and-revenue curve.

## Output

```
  reserve $0.0: fill 1.00, expected revenue $0.00
  reserve $0.5: fill 0.67, expected revenue $0.33
  reserve $0.8: fill 0.47, expected revenue $0.37
  reserve $1.0: fill 0.33, expected revenue $0.33
  reserve $1.2: fill 0.20, expected revenue $0.24

reading: a zero reserve fills every slot at zero price; a high
reserve prices each sale high but sells few. The revenue-maximizing
reserve sits between the two — the optimum is a property of the
demand curve, which is why it is estimated, not guessed.
```

## Notes

- A zero reserve fills every slot at zero price; expected revenue peaks
  at \$0.37 around a \$0.8 reserve, then falls as fill collapses.
- The revenue-maximizing reserve is a property of the demand curve,
  which is why it is estimated from bid data, not guessed.
