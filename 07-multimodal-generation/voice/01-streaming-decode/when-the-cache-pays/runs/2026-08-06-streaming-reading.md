# Run — the KV cache on audio tokens: correctness and the latency curve

**Date:** 2026-08-06
**Command:** `uv run python core/streaming_reading.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded JSON).
**Cost:** \$0 (local lane; the underlying run was the stage's recorded one).

## Purpose

Stage 01's recorded run answered the mission's central question — does the
serving mechanism built for text work unchanged for audio? This run reads
the recorded correctness contract (the two paths must produce identical
tokens) and lays out the latency table the verdict rests on.

## Output

```
eval clips: 3, tokens_match: 3/3
prompt tokens: 16, generated tokens/clip: 48
reconstruction MSE: 0.3205 .. 0.4280

recorded latency stress (500-token stream, p50 ms):
  naive:  first-10 1.43ms  last-10 9.81ms  (6.9x slower)
  cached: first-10 1.15ms  last-10 1.50ms  (roughly flat)
```

## Notes

- Correctness holds token-for-token: naive and cached produce identical
  completions on all 3 eval clips (tokens_match 3/3). The cache is not a
  different answer; it is the same answer at flat latency.
- The naive path degrades 6.9x over a 500-token stream (1.43 -> 9.81ms
  p50) because it recomputes the whole prefix each step; the cached path
  stays flat (1.15 -> 1.50ms). On a long audio stream the naive degradation
  is the real-time killer, and the cache is what makes the mission's
  streaming claim hold.
- Reconstruction MSE (0.32-0.43) is the codec's quality at this scale,
  separate from the decode-path latency this chapter is about.
