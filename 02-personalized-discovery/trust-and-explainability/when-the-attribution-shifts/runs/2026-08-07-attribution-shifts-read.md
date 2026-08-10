# Run — when the attribution shifts, executed on the baseline read

**Date:** 2026-08-07
**Command:** `uv run python core/attribution_shifts.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 52's detour: the explanation headline is not a stable property of
the item — it changes with the counterfactual the attribution tool
subtracts. This run computes the same item's contributions against the
zero baseline and the population-mean baseline, and reads the headline
flip.

## Output

```
attribution shifts, read (largest contribution per baseline):
  feature                   zero baseline  mean baseline
  price                           -0.0240        -0.0016
  category affinity               +0.0080        -0.0120
  similar users bought            +0.0198        +0.0011
  you viewed this category        +0.0140        +0.0053

  zero-baseline headline:  'similar users bought'
  mean-baseline headline:   'you viewed this category'

reading: the same item, the same model, the same score -
the headline flips from 'similar users bought' (unverifiable)
to 'you viewed this category' (verifiable) when the baseline
changes from zero to the population mean. Neither number is
wrong; attribution is defined against the counterfactual.
The question for the product is which counterfactual matches
what the user would compare against - the baseline the
explanation tool picks decides which claim the user sees.
```

## Notes

- The same item's headline flips from 'similar users bought'
  (unverifiable) under the zero baseline to 'you viewed this category'
  (verifiable) under the mean baseline; the score is unchanged.
- Neither attribution is wrong — each is a correct statement against a
  different counterfactual. Shapley-value-based attribution (Lundberg &
  Lee, NeurIPS 2017) makes the reference distribution explicit because
  the answer changes with it; the production fix is to pin the baseline
  to the comparison users actually make and audit headline stability.
