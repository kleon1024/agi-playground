# Run — the three-way verdict, re-run against current state

**Date:** 2026-08-06
**Command:** `uv run python core/three_way_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.05s (re-runs the stage's own report).
**Cost:** \$0 (local lane).

## Purpose

Stage 05's report is a verdict space of MET, NOT MET, and CANNOT DETERMINE.
This run re-runs the stage's own report against the real current state and
lays out the refusal's shape.

## Output

```
VERDICT: CANNOT DETERMINE
This report will not guess. The following inputs are missing: (18 named)
```

## Notes

- The third verdict value names exactly which input is missing, so the gap
  is a checklist, not a wall.
- No stage has produced the integrated outcome artifact yet; the refusal is
  the correct output for the mission's current state.
