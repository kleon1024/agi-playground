# Run — when the drift is silent, executed on the offline-versus-online read

**Date:** 2026-08-07
**Command:** `uv run python core/silent_drift.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 47's detour: the offline eval reuses the training distribution, so
a serving-time break leaves it unchanged. This run reads offline NDCG and
the online gap side by side.

## Output

```
drift is silent, read (offline vs online by hour):
  hour  offline ndcg  predicted  observed  gap
    0  0.712        0.040     0.039     0.001
    4  0.712        0.040     0.036     0.004
    8  0.712        0.040     0.023     0.017
   12  0.711        0.040     0.020     0.020

reading: offline NDCG is flat at 0.712 across all twelve
hours while observed CTR halves. The offline number is not
lying - it is blind: its labels come from the same broken
feed. The gap panel is the one that changes, which is why
monitoring lives online, not in the eval harness.
```

## Notes

- Offline NDCG stays at 0.712 while observed CTR halves from 0.039 to 0.020.
- The offline number is not lying — it is blind: its labels come from the same broken feed, which is why monitoring lives online.
