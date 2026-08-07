# Run — the two-environment null, read from the recorded full-chain report

**Date:** 2026-08-06
**Command:** `uv run python core/two_env_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded report).
**Cost:** \$0 (local lane).

## Purpose

Stage 05 elevated the null across two environments. This run reads the
recorded report and lays out the two-environment shape of the verdict.

## Output

```
  null result (100% degenerate steps, 0% eval success) = True
  VERDICT: MET (as an honest null result, extended across two environments)
```

## Notes

- The null repeated across two environments is a stronger claim than one
  failure: the verdict is the pattern, not either environment's number.
- The acceptance bar's second disjunct ("OR reports an honest null result")
  is what makes MET the correct reading over NOT MET.
