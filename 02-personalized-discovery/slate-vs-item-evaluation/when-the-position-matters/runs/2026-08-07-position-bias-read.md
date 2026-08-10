# Run — when the position matters, executed on the position-bias read

**Date:** 2026-08-07
**Command:** `uv run python core/position_bias.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 34 evaluates slates. This run reads why clicks lie about quality:
the click probability is relevance times the per-slot examination
probability, so an item's observed click rate depends on where it sits.

## Output

```
position bias, read (click probability per served slot):
  slot 1: y relevance 0.90 x examine 1.00 = click 0.900
  slot 2: z relevance 0.80 x examine 0.60 = click 0.480
  slot 3: x relevance 0.95 x examine 0.30 = click 0.285
  relevance best: x; most clicked: y

reading: the best item (x, 0.95) sits in slot three and gets
clicked 0.285; the promoted item (y, 0.90) in slot one gets
clicked 0.900. Clicks rank y above x — an evaluation that
reads clicks as quality measures the slot, not the item.
De-bias for position (examination models, position-weighted
metrics) before clicks become labels or a verdict (Craswell
et al. 2008).
```

## Notes

- The best item by relevance (x, 0.95) is the least clicked (0.285)
  because it sits in slot three; the promoted item (y, 0.90) in slot
  one is the most clicked (0.900).
- Clicks therefore rank y > z > x while relevance says x > y > z — an
  evaluation that reads clicks as quality measures the slot, not the
  item. De-bias for position (examination models such as Craswell et
  al. WSDM 2008, position-weighted metrics) before clicks become
  labels or a verdict.
