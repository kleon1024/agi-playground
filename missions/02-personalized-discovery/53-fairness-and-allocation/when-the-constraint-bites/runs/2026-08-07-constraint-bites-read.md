# Run — when the constraint bites, executed on the floor sweep

**Date:** 2026-08-07
**Command:** `uv run python core/constraint_bites.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 53's detour: a per-category minimum exposure lifts the tail and
costs aggregate CTR. This run sweeps the floor and reads the cost curve.

## Output

```
constraint bites, read (floor vs aggregate ctr):
  floor 0%: tail exposure 1%, aggregate ctr 0.0355
  floor 5%: tail exposure 5%, aggregate ctr 0.0345
  floor 10%: tail exposure 9%, aggregate ctr 0.0334
  floor 20%: tail exposure 15%, aggregate ctr 0.0307

reading: the first ten points of floor move the tail from
1% to 9% and cost 0.0021 aggregate CTR; the next ten move
it only to 15% and cost more (0.0027) per point of exposure.
The constraint curve is where the allocation decision lives -
how much relevance the platform is willing to spend on how
visible a tail.
```

## Notes

- The first ten points of floor move the tail from 1% to 9% for 0.0021 CTR; the next ten cost more per point for less reach.
- The constraint curve is where the allocation decision lives — how much relevance the platform spends on how visible a tail.
