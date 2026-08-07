# Run — when retraining flips the metric, executed on the offline-versus-online read

**Date:** 2026-08-07
**Command:** `uv run python core/retrain_flips.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 46's detour: retraining on fresh data raises the offline metric
while the served slate clicks less. This run reads both metrics for the
old and retrained models.

## Output

```
retrain flips the metric, read (old model vs retrained):
  offline ndcg@5: old 0.917 -> new 1.000
  exposure-weighted ctr: old 0.0289 -> new 0.0282

reading: the retrained model scores higher on the offline
list, but the slate it serves clicks less where it matters.
The offline labels were logged under the old policy, where
the top position inflated its own clicks; NDCG believes
that log, and the online page does not. The retrain decision
needs the metric that matches the goal - and an A/B, because
the exposure shift is only visible online.
```

## Notes

- Offline NDCG rises 0.917 to 1.000 while exposure-weighted CTR falls 0.0289 to 0.0282.
- The retrain decision needs the metric that matches the goal, and an A/B, because the exposure shift is only visible online.
