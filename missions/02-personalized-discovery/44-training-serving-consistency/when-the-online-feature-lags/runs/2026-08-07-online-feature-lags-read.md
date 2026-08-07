# Run — when the online feature lags, executed on the staleness read

**Date:** 2026-08-07
**Command:** `uv run python core/online_lag.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 44's detour: prices update after the training snapshot. This run
reads the logged estimate against the live value per item.

## Output

```
online feature lags, read (stale estimate vs live reality):
  item   logged price  live price  logged ctr  live ctr
  P1001   $49         $56         0.042      0.026
  P1002   $89         $89         0.023      0.026
  P1003   $19         $24         0.018      0.030

reading: P1001 and P1003 changed price after the snapshot;
their logged CTRs describe the old prices. The estimate is
not wrong - it is stale. The lag between the snapshot and
the live value is the skew, and it is a pipeline property,
not a model one.
```

## Notes

- P1001 and P1003 changed price after the snapshot; their logged CTRs describe the old prices.
- The estimate is not wrong — it is stale; the lag is a pipeline property, not a model one.
