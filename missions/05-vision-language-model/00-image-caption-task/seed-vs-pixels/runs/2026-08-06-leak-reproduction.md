# Run — leakage guardrail reproduction: seeds, pixels, and rejection

**Date:** 2026-08-06
**Command:** `uv run python core/leak_reproduction.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; reuses the stage's `generate_dataset.py`
unmodified.
**Wall-clock:** 1.4s (2,400 renders + hashing).
**Cost:** \$0 (local lane).

## Purpose

Stage 00's recorded run documents three states of its leakage guardrail
(naive -> rejection -> widened space). This run reproduces the mechanism on
the current (final) generator: the naive adjacent-seed split's collision
count, and the fixed split's rejection count plus its distortion.

## Output

```
train=2000 eval=400
train-internal pixel-hash duplicates: 79
naive (adjacent seeds, no rejection): collisions=17
fixed (rejection past 100000): collisions=0, rejected=29
single-shape images: train=696, naive-eval=126, fixed-eval=105
```

## Notes

- The fixed row exactly matches the recorded attempt-3 final run (rejected
  29, collisions 0, single-shape 105, train duplicates 79): the current
  generator is the widened-space version, and this run confirms it is
  deterministic and unchanged.
- The naive row (17 collisions, adjacent seeds) shows the leak mechanism
  still exists even in the widened space: disjoint seed streams do not imply
  disjoint renders, so without pixel-level rejection the birthday paradox
  produces train/eval collisions. The recorded attempt-1 measured 116
  collisions in the original narrow space (3,600-fold smaller per bucket);
  the number depends on the space and the ranges, the mechanism does not.
- The rejection burden (29 now vs 507 then) and the single-shape bucket
  (105 now vs 0 then) measure how the widening fixed the sampler's
  distortion: with a 3,600-state bucket, rejection no longer silently
  empties it.
