# Run — the model-fallback audit

**Date:** 2026-08-08
**Command:** `uv run python core/model_fallback.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.06s.
**Cost:** \$0 (local lane).

## Purpose

The stage's audit shows the total pipeline's p99 blows the 100ms
deadline. This detour isolates the model stage: the heavy inference
model (nominal 25ms slot) has its own heavy tail, and when it runs
long the request cannot win. The fix is a cascade — a fast fallback
model for requests that arrive at the model stage late. It serves
10,000 requests (fixed seed) under two policies: heavy-model-only,
and a cascade that switches to a cheaper model when the elapsed time
before inference is already high.

## Output

```
model-fallback audit: 10,000 requests, fixed seed
heavy model median 25ms (sigma 0.5); cheap fallback median
8ms; non-model stages 55ms; deadline 100ms

          policy     p50     p95     p99    mean  timeouts
      heavy-only    81.5   118.7   140.3    84.3   1800 (18.0%)
         cascade    75.5   103.9   125.3    77.8    693 (6.9%)

fallback share: 33.1% of requests
served by the cheap model
```

## Notes

- Heavy-model-only times out 18.0 percent of requests (1,800 of
  10,000) with a p99 of 140.3ms — the model stage's own tail is the
  deadline breaker. The cascade, switching to the cheap model when the
  request arrives late at the model stage, cuts timeouts to 6.9
  percent (693) and drops the p95 from 118.7 to 103.9ms.
- The trade is bid quality: 33.1 percent of requests are served by the
  cheap model — exactly the late, tail requests whose context data is
  the least certain. The cascade recovers the deadline at the price of
  worse bids on the worst-tail traffic.
- Latencies drawn lognormal with declared medians and spreads, fixed
  seed. Illustrative and deterministic, not real serving logs.
