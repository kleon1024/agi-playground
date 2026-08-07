# Run — the reserve interacting with eCPM, executed on the combined decision

**Date:** 2026-08-06
**Command:** `uv run python core/reserve_ecpm.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 14's reserve floors the auction; stage 15's eCPM ranks the ads. This
run combines them.

## Output

```
  reserve 0: eligible Ad A (100), Ad B (150), Ad C (120)
  reserve 100: eligible Ad A (100), Ad B (150), Ad C (120)
  reserve 125: eligible Ad B (150)
  reserve 160: eligible none
```

## Notes

- The reserve filters the eCPM ranking — at reserve 125 only Ad B (150)
  clears it; at 160 nothing does.
- The reserve and the ranking are one decision: what the platform refuses
  to show, and in what order.
