# Run — the PARTIAL verdict, read bullet by bullet

**Date:** 2026-08-06
**Command:** `uv run python core/partial_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded outcome report).
**Cost:** \$0 (local lane).

## Purpose

Stage 05's outcome report returns PARTIAL on exactly one of seven bullets.
This run reads the recorded report and prints the bullet-1 structure that
makes the verdict PARTIAL rather than MET or NOT MET.

## Output

```
bullet 1 of the outcome report, read:
  pooled: harness 18/18 vs no-harness 4/18 (private set)
  per tier: haiku DECISIVE (+1.000), sonnet DECISIVE (+0.833),
            opus inside spread -- no result
  public set: harness 6/6, but no no-harness control exists to compare
  -> PARTIAL: private decisive on haiku/sonnet, no result on opus,
     public half CANNOT DETERMINE, not MET
```

## Notes

- PARTIAL is narrower than NOT MET: 6 of 7 bullets are MET, and the one
  that is not names exactly which comparison is missing.
- The opus row is a no-result (margin inside run-to-run spread at N=2
  tasks), and the public half is CANNOT DETERMINE because the no-harness
  control was never run there — two different reasons, one verdict.
