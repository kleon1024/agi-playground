# Run — long-context grounding, executed on the window sweep

**Date:** 2026-08-07
**Command:** `uv run python core/long_context.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 36 resolves follow-ups through session context. This run grows a
session past the context window and reads where the first-turn
grounding falls out.

## Output

```
long context, read (first-turn grounding vs window):
  session turns  turn-1 kept  resolution
  4              yes         1.0
  8              yes         1.0
  9              no          0.8
  12             no          0.2
  24             no          0.1

reading: truncation drops the oldest turns first, so the
first-turn topic is the first grounding to fall out of the
window. A follow-up that says 'back to the first pair' needs
exactly that turn — pin it, or compress the middle turns
instead of dropping the oldest.
```

## Notes

- Truncation is oldest-first, so the first-turn topic drops first;
  resolution of "back to the first pair" falls from 1.0 to 0.1 as the
  grounding recedes.
- The shape matches the long-context finding that models use the
  beginning and end of the input far better than the middle (Liu et
  al., "Lost in the Middle", TACL 2024).
- The fix is retention, not a bigger window: pin the first-turn
  grounding or compress the middle turns.
