# Run — the funnel shape, read from the recorded sample run

**Date:** 2026-08-06
**Command:** `uv run python core/funnel_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the funnel run was the stage's recorded).

## Purpose

Stage 00's 3,000-document sample recorded the funnel at every gate. This
run reads the record and lays out the shape.

## Output

```
  text extracted      2,699 docs (90.0% of raw)
  english               947 docs (31.6% of raw)
  gopher quality        755 docs (25.2% of raw)
  c4 line filter        569 docs (19.0% of raw)
  minhash dedup         550 docs (18.3% of raw)
```

## Notes

- 31.6% of raw HTML is English and 18.3% survives to the clean set.
- The funnel is the audit trail, and the drop-reason table makes each
  gate's decision accountable.
