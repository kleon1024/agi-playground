# Run — when the take rate is too high, executed on the collapse read

**Date:** 2026-08-07
**Command:** `uv run python core/rate_too_high.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 42's take rate trades volume against revenue per transaction. This run sweeps the rate past its peak and reads the collapse.

## Output

```
take rate too high, read:
  rate 30%: volume 520, revenue $156
  rate 50%: volume 200, revenue $100
  rate 70%: volume 0, revenue $0
  rate 85%: volume 0, revenue $0

reading: revenue peaks around 30-40% and collapses past 70%.
At 85% the volume is nearly gone and revenue is a fraction of
the peak — the platform's greed is measured in lost volume,
which is the same shape as the reserve and ad-load decisions.
```

## Notes

- Revenue peaks around 30-40% and collapses past 70%; at 85% the volume is nearly gone.
- The platform's greed is measured in lost volume — the same shape as the reserve and ad-load decisions.
