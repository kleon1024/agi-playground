# Run — when the tail costs, executed on the mean-versus-tail read

**Date:** 2026-08-07
**Command:** `uv run python core/tail_costs.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.05s.
**Cost:** \$0 (local lane).

## Purpose

Stage 49's detour: mean service time suggests one capacity; the tail
demands another. This run serves a 17ms-mean service at fractions of its
mean capacity and reads the deadline misses.

## Output

```
tail costs, read (mean service 17ms -> mean capacity 59 req/s):
  50% of mean capacity (29 req/s): p50 10ms, p99 242ms, over 100ms 16.8%
  80% of mean capacity (47 req/s): p50 71ms, p99 519ms, over 100ms 43.6%
  100% of mean capacity (59 req/s): p50 1144ms, p99 4112ms, over 100ms 94.3%

reading: at the capacity the mean suggests, a tenth of
queries miss the deadline; at half that load the tail still
dominates the p99. Provisioning on the mean is how a
service 'at capacity' spends its budget failing the slow
queries the mean never saw.
```

## Notes

- At 100% of mean capacity, 94.3% of queries miss the 100ms deadline; even at 50% the p99 is 242ms.
- Provisioning on the mean is how a service 'at capacity' spends its budget failing the slow queries the mean never saw.
