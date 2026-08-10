# Run — the capacity audit over the emitted load scan

**Commands:** `uv run python core/capacity.py --emit-log /tmp/capacity-envelope.json`;
`uv run python prod/capacity_audit.py /tmp/capacity-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 49's read shows the tail at three loads. This run is the
case-finding half of the stage: capacity is found by load-testing with
a deadline, not by arithmetic on the mean. The core script emits the
per-load scan; the production audit reads the load at which the
deadline percentile is met and names what the number means.

## Output

```
capacity audit (deadline 100ms, mean service 17ms, 5% at 150ms):
  load  util    p50   p95   p99 over deadline
    20   34%  10 150 170         10.3%
    30   51%  10 150 267         17.9%
    40   68%  10 250 370         28.4%
    45   76%  44 324 459         37.8%
    50   85%  100 460 620         48.4%
    55   94%  192 745 933         68.8%
    60  102%  1850 3003 3223         94.2%

verdict: DEADLINE UNACHIEVABLE -- p95 of the service mix
(150ms) exceeds the 100ms
deadline at every load, because the 5% slow service
(150ms) is itself over the deadline. No
machine count satisfies a p95 deadline tighter than the
service tail; the mean capacity
(59 req/s) is the divergence load, not a
serving answer. The fix is cutting the service tail -
hedge, timeout, parallel shards - before adding machines.
```

## Notes

- p95 of the service mix (150ms) exceeds the 100ms deadline at every
  scanned load, so the verdict is DEADLINE UNACHIEVABLE: the 5% slow
  service is itself over the deadline, and no machine count satisfies a
  p95 deadline tighter than the service tail.
- The mean capacity (59 req/s) is the divergence load — where the queue
  grows without bound — not the load where the deadline is met; the
  audit's message is that capacity planning that skips the load test
  confuses the two (Dean and Barroso, "The Tail at Scale",
  Communications of the ACM, 2013).
