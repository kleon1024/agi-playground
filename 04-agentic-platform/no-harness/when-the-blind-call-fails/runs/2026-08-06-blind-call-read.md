# Run — the blind call, read per tier from the recorded matrix

**Date:** 2026-08-06
**Command:** `uv run python core/blind_call_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded 18-row JSONL).
**Cost:** \$0 (local lane; the underlying calls were the stage's recorded
2026-08-01 spend).

## Purpose

Stage 01's recorded matrix is the mission's control: one blind call per
task, no tools, no feedback, no retry. This run reads the recorded JSONL
and lays out per-tier resolve and the cost of one success.

## Output

```
no-harness (one blind call), read per tier:
  haiku   0/6 resolved  $  0.49 total  (never resolved)
  opus    3/6 resolved  $  3.28 total  $  1.09/resolved
  sonnet  1/6 resolved  $  1.37 total  $  1.37/resolved

reading: the loop is worth nothing if a blind call does the job,
and worth everything where it cannot — resolve, not cost per
attempt, is the number the mission turns on.
```

## Notes

- Haiku never resolved (0/6) — the cheapest arm buys nothing at this task
  difficulty, and its \$0.49 is pure cost.
- Opus is cheapest per resolved (\$1.09) despite costing the most per
  attempt: a lower-resolving arm can still cost more per success, and a
  more-expensive arm can be cheapest per success.
- Cost per attempt flatters whichever model fails fastest, which is why the
  mission's metric is dollars per resolved task, not per attempt.
