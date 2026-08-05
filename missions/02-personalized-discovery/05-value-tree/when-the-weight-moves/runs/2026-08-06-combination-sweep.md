# Run — the weight sweep across both combination functions

**Date:** 2026-08-06
**Command:** `uv run python core/combination_sweep.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; reuses the stage's `value_tree.py`
unmodified.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 05's recorded run swept one weight; this run quantifies the mechanism
on the same 12-item set: how the ranking flips as the satisfaction weight
sweeps 0 to 1 under both combination functions, and where they disagree.

## Output

```
12 items, 4 archetypes (0 = click-shaped, 1 = quality-shaped, else mixed)
w_sat   additive top-1  multiplicative top-1
 0.00           item_8               item_8
 0.33           item_8              item_11
 0.67           item_5               item_6
 1.00           item_1               item_1

at w_sat=0.5, the click-shaped item's rank under each function:
  additive: rank 8/12 (score 0.482)
  multiplicative: rank 11/12 (score 0.300)
```

## Notes

- The top-1 item changes with the weight in both functions, and the two
  functions disagree at w_sat=0.33 and 0.67: the same predictions, the same
  weights, different winners — the combination function is itself a strategy
  choice.
- At w_sat=0.5 the click-shaped item (item_0) ranks 8/12 additive (0.482)
  and 11/12 multiplicative (0.300): the product's near-zero-satisfaction
  punishment is what collapses it, exactly the substitutes-versus-
  requirements claim in the stage's docstring, measured.
- Both functions converge on item_1 (the quality-shaped item) at w_sat=1.0 —
  when satisfaction is everything, the function no longer matters.
