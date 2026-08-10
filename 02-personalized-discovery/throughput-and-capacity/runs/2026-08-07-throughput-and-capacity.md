# Run — throughput and capacity, executed on the queue simulation

**Date:** 2026-08-07
**Commands:** `uv run python core/capacity.py --emit-log /tmp/capacity-envelope.json`;
`uv run python prod/capacity_audit.py /tmp/capacity-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 49 introduces capacity planning. This run simulates a queue with
10ms mean service and 5% of queries at 150ms, and reads the latency
percentiles at three loads, then scans arrival rates from 20 to 60 req/s
for the audit.

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

capacity scan (deadline 100ms):
  load  util    p50   p95   p99 over 100ms
    20   34%  10 150 170      10.3%
    30   51%  10 150 267      17.9%
    40   68%  10 250 370      28.4%
    45   76%  44 324 459      37.8%
    50   85%  100 460 620      48.4%
    55   94%  192 745 933      68.8%
    60  102%  1850 3003 3223      94.2%

  mean-service capacity (divergence load): 59 req/s.
```

## Notes

- At 55 req/s the p99 is 933ms against a 10ms p50, and 68.8% of queries miss the 100ms deadline.
- Capacity planning is throughput times deadline, not throughput times average latency.
- The scan shows p95 already at 150ms at 20 req/s (34% utilization):
  the 5% slow service is itself over the 100ms deadline, so no load
  satisfies a p95 deadline — the audit reads this as DEADLINE
  UNACHIEVABLE and the fix as cutting the service tail, not adding
  machines.
