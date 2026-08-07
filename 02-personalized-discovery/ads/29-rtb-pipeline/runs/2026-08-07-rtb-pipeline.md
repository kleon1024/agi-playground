# Run — RTB pipeline, executed on the latency-budget model

**Date:** 2026-08-07
**Command:** `uv run python core/rtb_latency.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 29 asks where a real-time bid's 100ms deadline goes. This run
sums the pipeline stages and reads the margin left.

## Output

```
RTB budget, read (100 ms):
  request parse: 5 ms
  user profile lookup: 20 ms
  context features: 10 ms
  model inference: 25 ms
  bid decision: 15 ms
  response send: 5 ms
  total: 80 ms, margin 20 ms

reading: five stages consume 80 ms, leaving 20 ms of margin.
Every stage is a latency source and a potential timeout — the
pipeline's p95 is the sum of its worst stages, which is why RTB
engineering is mostly about keeping the tail inside the budget.
```

## Notes

- Five stages consume 80ms of the 100ms deadline, leaving 20ms of
  margin — and the margin is what absorbs jitter.
- The p95 is the sum of the worst stages, which is why the
  when-the-bidder-is-slow detour treats latency as a selection
  mechanism.
