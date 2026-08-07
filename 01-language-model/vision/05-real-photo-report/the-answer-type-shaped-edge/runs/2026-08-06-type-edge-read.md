# Run — the answer-type-shaped edge, recomputed from the recorded API log

**Date:** 2026-08-06
**Command:** `uv run python core/type_edge_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded 198-row JSONL).
**Cost:** \$0 (local lane; the API calls were the stage's recorded spend).

## Purpose

Stage 05's report found the hosted API's edge is answer-type-shaped. This
run recomputes the per-type split from the raw log.

## Output

```
  yes_no     51/80 (0.637)
  other      34/93 (0.366)
  number     6/25 (0.240)
```

## Notes

- The recomputation reproduces the recorded report exactly — the type split
  is the log's own numbers, not prose.
- The API is strongest on the easiest type (yes/no) and weakest where
  counting is required (number), which is where a future build could
  compete.
