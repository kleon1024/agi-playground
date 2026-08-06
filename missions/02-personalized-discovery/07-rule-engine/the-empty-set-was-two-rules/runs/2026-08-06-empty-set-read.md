# Run — the empty set that was two rules' fault, read from the record

**Date:** 2026-08-06
**Command:** `uv run python core/empty_set_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the policy evaluation was the stage's recorded).

## Purpose

Stage 07's run holds the sharpest interaction: EU regional and safety rules
each remove part of the set, and applied together they empty it. This run
reads the record and lays out the per-rule counts and the joint failure.

## Output

```
  US request removed 10/16 by region and kept 6.
  Tightening the cap from 2 to 1 kept 3 and capped 3.
  EU regional and safety rules jointly emptied the set;
  each alone removed 6/16 and 10/16 respectively.
```

## Notes

- Each rule alone leaves survivors; the joint application empties the set —
  a rule engine's failure mode is interaction, not any single rule.
- Precedence and the empty-set check are part of the engine, not
  post-processing.
