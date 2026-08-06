# Run — the collision that closed the gap, read from the recorded dataset run

**Date:** 2026-08-06
**Command:** `uv run python core/collision_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the dataset generation was the stage's recorded
run).

## Purpose

Stage 00's first dataset generation used disjoint seed ranges and still
collided. This run reads the record and lays out both defects and the fix.

## Output

```
  collisions under disjoint seed ranges: 116
  second defect: the eval single-shape bucket came out empty
  fix: widening each shape's size and position space
```

## Notes

- Disjoint seeds are not disjoint images: the state space is small enough
  that collisions happen across streams.
- The leakage guardrail must check pixels, not seeds — the collision is the
  evidence, and the empty-bucket defect is what a pixels-only check misses.
