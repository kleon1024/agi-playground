# Run — when the fusion weight moves, executed on the weighted-sum model

**Date:** 2026-08-07
**Command:** `uv run python core/fusion_weight.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 21 fuses lexical and dense scores. This run sweeps the fusion
weight and reads which matcher's winner takes the top slot.

## Output

```
fusion weight, read (score = w*lex + (1-w)*dense):
  w=0.0: winner d2 (0.90)
  w=0.5: winner d1 (0.65)
  w=1.0: winner d1 (0.90)

reading: at w=0 dense wins (d2, 0.90), at w=1 lexical wins
(d1, 0.90), and at w=0.5 d1 leads by 0.05. The weight is the
product decision: how much the platform trusts meaning versus
exact terms.
```

## Notes

- At w=0 the dense-only winner (d2) takes the slot; at w=1 the
  lexical-only winner (d1) does; at w=0.5 the blend edges to d1.
- The weight is a product decision about how much the platform trusts
  meaning versus exact terms, not a tuning constant.
