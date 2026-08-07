# Run — throughput and capacity, executed on the queue simulation

**Date:** 2026-08-07
**Command:** `uv run python core/capacity.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 49 introduces capacity planning. This run simulates a queue with
10ms mean service and 5% of queries at 150ms, and reads the latency
percentiles at three loads.

## Output

```
throughput and capacity, read (10ms service, 5% at 150ms):
  20 req/s: p50 10ms, p95 150ms, p99 170ms, over 100ms 10.3%
  40 req/s: p50 10ms, p95 250ms, p99 370ms, over 100ms 28.4%
  55 req/s: p50 192ms, p95 745ms, p99 933ms, over 100ms 68.8%

reading: service averages 17ms, so the naive capacity is
roughly 59 req/s. The tail grows first: at 55 req/s the p99
is many times the p50 and a real share of queries miss the
100ms deadline. Capacity planning is throughput x deadline,
not throughput x average latency.
```

## Notes

- At 55 req/s the p99 is 933ms against a 10ms p50, and 68.8% of queries miss the 100ms deadline.
- Capacity planning is throughput times deadline, not throughput times average latency.
