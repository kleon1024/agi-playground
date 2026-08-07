# Run — absence as a signal, executed on the exposure log

**Date:** 2026-08-07
**Command:** `uv run python core/absence_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 00 models interactions. This run separates the two zeros in a log:
an item shown and not clicked (implicit negative) versus an item never
shown (no information).

## Output

```
  A: shown 1000x, 120 clicks -> ctr 0.120
  B: shown 1000x, 4 clicks -> ctr 0.004
  C: shown 1000x, 0 clicks -> implicit negative
  D: never shown -> no signal
```

## Notes

- A zero click after 1000 exposures is a real negative; a zero with zero
  exposure is silence.
- Treating them alike rewards never-shown items and punishes honest
  failures.
