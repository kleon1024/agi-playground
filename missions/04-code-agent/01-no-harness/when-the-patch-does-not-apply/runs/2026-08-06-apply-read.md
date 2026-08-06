# Run — the diff that never applied, read from the recorded no-harness run

**Date:** 2026-08-06
**Command:** `uv run python core/apply_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded JSONL).
**Cost:** \$0 (local lane; the calls were the stage's recorded 2026-08-01
spend).

## Purpose

Stage 01 applies each blind call's diff with plain git apply, no retry.
This run reads the record and lays out the apply-vs-resolve relationship.

## Output

```
  haiku   1/6 diffs applied, 0/6 resolved
  sonnet  1/6 diffs applied, 1/6 resolved
  opus    3/6 diffs applied, 3/6 resolved
```

## Notes

- Application is the first gate: a diff that does not apply resolves
  nothing, and with no retry the gate is final.
- Applied and resolved coincide exactly except haiku (1 applied, 0
  resolved): the one haiku diff that applied still left the target test
  failing.
