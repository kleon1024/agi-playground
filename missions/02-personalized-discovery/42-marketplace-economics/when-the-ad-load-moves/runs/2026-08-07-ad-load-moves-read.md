# Run — when the ad load moves, executed on the displacement trade read

**Date:** 2026-08-07
**Command:** `uv run python core/ad_load.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 42 treats ad load as a marketplace decision. This run sweeps the number of ads and reads the revenue-versus-organic trade.

## Output

```
ad load, read (10 slots):
  0 ad(s): ad revenue $0.00, organic value $1.00, total $1.00
  1 ad(s): ad revenue $0.25, organic value $0.90, total $1.15
  2 ad(s): ad revenue $0.40, organic value $0.80, total $1.20
  3 ad(s): ad revenue $0.45, organic value $0.70, total $1.15

reading: each ad adds revenue but displaces an organic slot.
The total peaks before the maximum ad load — the same trade as
stage 18's externality, now set by the marketplace decision
of how many ads a page carries.
```

## Notes

- Total value peaks at two ads (\$1.20) and falls after — each ad adds revenue but displaces an organic slot.
- The same trade as stage 18's externality, now set by the marketplace decision of how many ads a page carries.
