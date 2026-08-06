# Run — the bimodal retry, read from the recorded closing-the-loop run

**Date:** 2026-08-06
**Command:** `uv run python core/bimodal_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded JSONL).
**Cost:** \$0 (local lane; the retry calls were the stage's recorded
2026-08-03 spend).

## Purpose

Stage 06 gave every failed no-harness attempt one retry turn with real
outcome feedback. This run reads the JSONL and lays out the bimodal split.

## Output

```
  haiku   6 retried, 0 diffs applied, 0 resolved
  sonnet  3 retried, 1 diffs applied, 1 resolved
  opus    3 retried, 1 diffs applied, 1 resolved
```

## Notes

- The retry is bimodal: either the corrected diff applied and the fix was
  correct, or git apply rejected it the same way as the first attempt.
- Ten of twelve corrected diffs were rejected — the feedback did not fix
  the apply failure.
