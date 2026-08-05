# Run — the hosted API on real photos, recomputed from the raw log

**Date:** 2026-08-06
**Command:** `uv run python core/real_photo_api.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded raw log).
**Cost:** \$0 (local lane; the API calls were the stage's recorded run).

## Purpose

Mission 05's real-photo report compared vision, text-only, and the hosted
API. This run recomputes the API's accuracy from the recorded raw log and
lays the three-arm comparison beside it.

## Output

```
hosted API (openai/gpt-4o-mini, 198 real-photo questions):
  overall: 91/198 = 0.460
  number       6/25   = 0.240
  other       34/93   = 0.366
  yes_no      51/80   = 0.637

three arms (recorded): vision 0.2374, text-only 0.2222, hosted 0.4596
```

## Notes

- The recomputed API accuracy (0.460) matches the recorded 0.4596 to
  rounding; the per-type split (24.0/36.6/63.7%) matches the recorded
  numbers — the log and the report agree.
- Vision beats text-only beyond its spread (+0.0152), and hosted beats
  vision by -0.2222 — the API dominates both arms, so the verdict is NOT
  MET on real photos exactly as on the synthetic set. The API's edge is
  largest on yes/no (63.7%) and weakest on number questions (24.0%).
