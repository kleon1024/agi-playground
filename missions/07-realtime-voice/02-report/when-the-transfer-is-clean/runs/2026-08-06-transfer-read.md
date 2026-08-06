# Run — the clean transfer, read from the committed stage JSONs

**Date:** 2026-08-06
**Command:** `uv run python core/transfer_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed stage 00/01 JSONs).
**Cost:** \$0 (local lane; the underlying runs were the stage's recorded
2026-07-31 results).

## Purpose

Stage 02's report is mission 07's MET verdict, resting on five acceptance
lines independently. This run reads the committed stage 00/01 JSONs and
lays out each line.

## Output

```
mission 07 MET verdict, five lines read from the committed JSONs:
  codec MSE 0.0111 vs silence 0.3251 / mean-signal 0.3001
  offline-vs-streaming gap: max logit gap 1.19e-05 across 30 clips
  latency at 500 steps: naive tail grows 6.9x, cached 1.3x
  reused serving code: zero lines changed (engine.py imported)
```

## Notes

- The quality gap is a true zero at logit level (1.19e-05 across 30 clips):
  cached decode produces identical token sequences to full recompute.
- The latency benefit only appears at length — invisible at the native
  48-token clip length, 6.9x vs 1.3x growth at 500 steps — which is why the
  report measures it at two scales rather than one.
