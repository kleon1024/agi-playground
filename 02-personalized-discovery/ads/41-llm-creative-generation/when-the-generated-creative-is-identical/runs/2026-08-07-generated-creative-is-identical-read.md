# Run — when the generated creative is identical, executed on the collapse read

**Date:** 2026-08-07
**Command:** `uv run python core/creative_collapse.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 41's generator can collapse. This run normalizes three generated variants and counts the distinct messages.

## Output

```
creative collapse, read (3 generated variants):
  'Run faster, pay less'
  'Run faster. Pay less.'
  'run faster pay less
  distinct after normalization: 2

reading: three variants collapse to two distinct messages, so
selection is choosing between a copy and a punctuation edit —
the scoring model cannot find real creative distance.
LLM generation needs a diversity control (temperature, 
repetition penalty) or the creative space shrinks to the
mode the model prefers.
```

## Notes

- Three variants collapse to two distinct messages — selection is choosing between a copy and a punctuation edit.
- LLM generation needs a diversity control (temperature, repetition penalty) or the creative space shrinks to the mode the model prefers.
