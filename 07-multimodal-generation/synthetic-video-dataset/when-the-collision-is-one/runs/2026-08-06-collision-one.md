# Run — the one-in-150 collision, read from the recorded dataset run

**Date:** 2026-08-06
**Command:** `uv run python core/collision_one.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the generation was the stage's recorded run).

## Purpose

Stage 00's generator extended mission 05's image space along time. This
run reads the recorded run and lays out why the collision problem shrank.

## Output

```
  only a single eval candidate needed rejecting, not hundreds
  116 train/eval collisions on the first attempt (mission 05, for contrast)
  state space: 3 shapes x 4 colors x 3 half-sizes x 8 directions x positions
  roughly two orders of magnitude over a single static image
```

## Notes

- Per-clip state space multiplies over the time axis, so collisions that
  dominated mission 05's static images nearly vanish.
- The generator's headroom is a property of the space, not the code.
