# Run — when the creative context changes, executed on the per-context model

**Date:** 2026-08-07
**Command:** `uv run python core/creative_context.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 26 selects creatives. This run scores two creatives across feed
and search contexts and reads the context-dependent winner.

## Output

```
creative context, read:
  rich card: feed 0.08, search 0.02
  compact: feed 0.03, search 0.06

reading: the rich card wins in the feed where users browse;
the compact creative wins on search where users scan. A single
global creative rank would pick the rich card everywhere and
leave search clicks on the table — context is a feature of the
selection model, not a label on top of it.
```

## Notes

- The rich card wins in the feed (0.08 vs 0.03); the compact creative
  wins on search (0.06 vs 0.02).
- A single global creative rank would pick the rich card everywhere —
  context is a feature of the selection model, not a label on top of
  it.
