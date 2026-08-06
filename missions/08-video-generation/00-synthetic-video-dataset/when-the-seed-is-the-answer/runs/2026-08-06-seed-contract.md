# Run — the seed contract, read from the fixture manifest

**Date:** 2026-08-06
**Command:** `uv run python core/seed_contract.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed fixture manifest).
**Cost:** \$0 (local lane; the fixtures were the stage's recorded 2026-07-31
generation).

## Purpose

Stage 00's committed fixtures hold the contract that makes a clip scoreable:
seed -> prompt -> motion -> frames, rendered deterministically. This run
reads the manifest and lays out the contract.

## Output

```
fixture manifest: 6 clips, seed -> prompt -> frames
  vid-0 seed 0: a yellow square moving down_right | square yellow, down_right speed 2 x0 11 y0 10 | 8 frames
  vid-1 seed 1: a red circle moving left | circle red, left speed 2 x0 25 y0 18 | 8 frames
  vid-2 seed 2: a red circle moving down_left | circle red, down_left speed 2 x0 19 y0 14 | 8 frames
```

## Notes

- The manifest records the seed, the prompt, the full motion dict (shape,
  color, half, direction, speed, start position), and the frame files — the
  complete answer key a later stage's completion is checked against.
- Determinism is the property that makes the check mechanical: the same
  seed renders the same frames, so "did the model produce the right
  frames" is a computed comparison, not a human judgment call.
