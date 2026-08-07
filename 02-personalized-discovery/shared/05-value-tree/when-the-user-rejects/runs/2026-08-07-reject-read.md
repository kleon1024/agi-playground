# Run — the user's no, executed on the value tree

**Date:** 2026-08-07
**Command:** `uv run python core/reject_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 05's value tree trades user value against revenue. This run shows
what an explicit dislike signal does to one item's score and the slate it
was in.

## Output

```
  x: value 0.8 revenue 0.3 -> score 0.65
  y: value 0.6 revenue 0.9 -> score 0.15
  z: value 0.5 revenue 0.2 -> score 0.40
  after user rejects x:
  x: value 0.0 revenue 0.3 -> score -0.15
  y: value 0.6 revenue 0.9 -> score 0.15
  z: value 0.5 revenue 0.2 -> score 0.40
```

## Notes

- One explicit negative rewrites the trade — the highest combined score
  can fall below the fold.
- The value tree is only as current as the signals feeding it.
