# Run — codebook usage trajectory, seed 7

**Date:** 2026-08-06
**Command:** `uv run --group torch python core/train_codec.py --steps 600 --usage-every 25 --seed 7 --out runs/codec-seed7-usage.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, MPS.
**Software:** Python 3.11.14 via uv; torch 2.13.0; the stage's own
`codec.py`/`train_codec.py` with the new `--usage-every` logging.
**Wall-clock:** ~2 minutes (600 steps).
**Cost:** \$0 (local lane).

## Purpose

The stage's recorded run (seed 0) ended healthy at 34/64 codes after a fix;
the earlier narrative recorded a collapse (1-2/64). This run measures the
usage trajectory itself on a fresh seed, with codebook bincounts logged every
25 steps, so the collapse-to-partition arc is data instead of a story.

## Metrics

```
step    unique/64   entropy ratio   note
   0       1/64         0.000      whole batch (2048 tokens) on ONE code
 100       2/64         0.033      second code barely alive
 200       2/64         0.033      still collapsed
 300      13/64         0.187      the codebook starts partitioning
 400      14/64         0.520      peak entropy
 500      12/64         0.409      non-monotonic — codes die and revive
 600      15/64         0.475      final: 15/64, partial collapse
```

Final: unique_codes_used 15/64, entropy 1.976, entropy_ratio 0.475, eval MSE
0.13476 against silence 0.32507 and mean_signal 0.29721 (beats both).

## Notes

- At step 0 the entire batch maps to one code and 63 codes are dead. Dead
  codes receive no straight-through gradient, so they stay dead unless the
  optimizer's movement of the live code's neighbours pulls the encoder
  across the boundary — which is why recovery is slow and seed-dependent.
- The trajectory is non-monotonic (14 -> 12 -> 15 unique codes), not a
  monotone recovery: the codebook can lose codes after gaining them.
- Seed-dependence is the point this run shares with the mission's later
  stages: seed 0 ends at 34/64, seed 7 at 15/64, from identical code. The
  collapse is a real, repeatable failure regime, not a one-off bug.
