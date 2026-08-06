# Run — the variance that decides, read from the breached fixture

**Date:** 2026-08-06
**Command:** `uv run python core/variance_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed fixture).
**Cost:** \$0 (local lane).

## Purpose

Stage 09's report rejects a positive mean gap not larger than its 95%
margin. This run reads the breached fixture's seed arrays and lays out the
variance math the verdict depends on.

## Output

```
  candidate nDCG@10 per seed: [0.412, 0.398, 0.421, 0.405, 0.415]
  popularity per seed:        [0.301, 0.309, 0.295, 0.303, 0.298]
  item-item CF per seed:      [0.356, 0.348, 0.362, 0.351, 0.359]
  candidate spread: 0.0230 vs gap to CF 0.0550
```

## Notes

- The gap to CF (0.0550) clears the candidate's own spread (0.0230) — the
  headline beats both baselines by more than seed variance.
- The verdict is still NOT MET because the cold-start guardrail fell below
  its baseline: variance is a veto input, not an appendix.
