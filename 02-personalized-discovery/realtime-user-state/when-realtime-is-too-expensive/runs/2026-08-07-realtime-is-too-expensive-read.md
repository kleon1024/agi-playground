# Run — when realtime is too expensive, executed on the p95 sweep

**Date:** 2026-08-07
**Command:** `uv run python core/realtime_cost.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 48's detour: realtime features must be computed per request. This
run measures the p95 as the feature count grows, against a 100ms
deadline.

## Output

```
realtime is too expensive, read (p95 per request, deadline 100ms):
   0 realtime features: p95 38ms (ok)
   5 realtime features: p95 58ms (ok)
  10 realtime features: p95 78ms (ok)
  20 realtime features: p95 118ms (over)

reading: the batch path alone sits at 38ms. Ten realtime
features push the p95 to 78ms - still inside the deadline;
twenty blow through it. Every feature added to the request
path is a latency budget spent, and the ones whose signal
does not change minute to minute belong in the batch path,
not on the critical one.
```

## Notes

- p95 climbs 38ms to 118ms as realtime features grow from 0 to 20; twenty blow through the 100ms deadline.
- Every feature on the request path spends the latency budget; signals that change slowly belong in the batch path.
