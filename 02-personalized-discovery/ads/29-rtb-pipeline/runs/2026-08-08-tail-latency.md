# Run — the tail-latency audit

**Date:** 2026-08-08
**Command:** `uv run python core/tail_latency.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.11s.
**Cost:** \$0 (local lane).

## Purpose

The stage run splits a 100ms budget across six pipeline stages. The
audit asks the case-finding question at production scale: what does
the deadline actually see? It draws 20,000 requests (fixed seed)
where each stage's latency is lognormal with the stage's nominal time
as the median and a declared spread (sigma 0.25), sums the stages, and
reads the total against the 100ms deadline.

## Output

```
tail-latency audit: 20,000 requests, fixed seed
six stages, lognormal latency with declared spread sigma 0.25

                  stage     p50     p90     p99
          request parse     5.0     6.9     9.0
    user profile lookup    19.9    27.4    36.1
       context features    10.0    13.8    17.9
        model inference    24.9    34.3    44.9
           bid decision    15.0    20.7    27.2
          response send     5.0     6.9     8.9

  total vs 100ms deadline:
    p50:  81.7 ms
    p90:  95.3 ms
    p95:  99.5 ms
    p99:  108.2 ms
    mean: 82.4 ms
    timed out (>100 ms): 933 (4.7%)
```

## Notes

- The p50 total sits near the nominal 80ms and the p95 (99.5ms) fits
  inside the deadline, but the p99 blows it at 108.2ms — 933 of 20,000
  requests (4.7 percent) exceed 100ms and are slots with no bid.
- The mean (82.4ms) hides the tail: the deadline is a tail constraint,
  and the margin has to be sized for the p99, not the p95. Every
  timed-out request is a lost auction before the bid is ever compared.
- Stage latencies drawn lognormal with declared medians and sigma 0.25,
  fixed seed. Illustrative and deterministic, not real serving logs.
