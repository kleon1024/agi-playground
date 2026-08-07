# Run — the real network round trip, read beside the decode budget

**Date:** 2026-08-06
**Command:** `uv run python core/network_reading.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded round-trip JSON).
**Cost:** \$0 (local lane; the round trip was the stage's recorded live
measurement).

## Purpose

Stage 03 measured a real Tailscale round trip beside the KV-cache
correctness. This run reads the round-trip JSON and lays it beside the
decode budget, so the realtime contract's two terms are one table.

## Output

```
real Tailscale round trip (200 pings, 64B each way):
  p50 9.66ms | p95 42.46ms | mean 15.11ms | max 85.25ms

vs the decode budget (cached path, ~1.5ms/token from stage 01):
  a 48-token completion decodes in ~72ms; the network p50 adds
  ~10ms, but the p95 (42ms) and max (85ms) round trips are a
  significant fraction of the budget — the tail is where the
  realtime contract lives.
```

## Notes

- The cached decode is flat (~1.5ms/token), so a 48-token completion is
  ~72ms of decode; the network p50 (9.7ms) is a small addition, but the
  p95 (42.5ms) and max (85.3ms) round trips are significant fractions of
  the budget — the network's tail, not the decode, is where realtime
  margin goes.
- The KV-cache correctness held on the real-speech vocabulary (max logit
  gap ~3e-05, 60/60 token sequences matched), so the decode side is
  trustworthy; the budget question is the network's, measured live over a
  DERP-relayed Tailscale path.
