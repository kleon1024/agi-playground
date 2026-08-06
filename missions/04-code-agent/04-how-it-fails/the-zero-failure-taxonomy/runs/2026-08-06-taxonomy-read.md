# Run — the zero-failure taxonomy, read from the recorded failure catalogue

**Date:** 2026-08-06
**Command:** `uv run python core/taxonomy_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded taxonomy text).
**Cost:** \$0 (local lane; the taxonomy was the stage's recorded run).

## Purpose

Stage 04 sorted every real attempt into failure categories. This run reads
the recorded taxonomy and lays out the two-arm contrast.

## Output

```
  resolved             harness 18/18  no-harness 4/18
  target_still_failing harness 0/18   no-harness 12/18
  regressed            harness 0/18   no-harness 0/18
  tampered             harness 0/18   no-harness 0/18
  no_tests_ran         harness 0/18   no-harness 0/18
  timeout              harness 0/18   no-harness 2/18
```

## Notes

- The harness arm's zero-failure rows are a real result: with tools and
  retries, no tier needed a second observation to notice a wrong patch.
- The no-harness arm is where failures live (12 target_still_failing,
  2 timeouts).
