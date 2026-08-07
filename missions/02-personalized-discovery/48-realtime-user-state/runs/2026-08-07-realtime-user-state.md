# Run — realtime user state, executed on the session-boost read

**Date:** 2026-08-07
**Command:** `uv run python core/session_state.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 48 introduces real-time personalization. This run ranks one slate
with the batch model's learned priors and with a session boost for a user
who dwelled on an audio item.

## Output

```
real-time user state, read (user dwelled 40s on P1001, 3 min ago):
  batch order (learned ctr):
    1. P1001 (audio, ctr 0.032)
    2. P1002 (audio, ctr 0.030)
    3. P1003 (cable, ctr 0.028)
    4. P1004 (cable, ctr 0.025)
    5. P1005 (cases, ctr 0.020)
    6. P1006 (cases, ctr 0.018)
  realtime order (session boost):
    1. P1001 (audio, score 0.041)
    2. P1002 (audio, score 0.039)
    3. P1003 (cable, score 0.028)
    4. P1004 (cable, score 0.025)
    5. P1005 (cases, score 0.020)
    6. P1006 (cases, score 0.018)

reading: the session pulled audio up and cases down.
The batch model would need a retrain to learn what the
session knows from one dwell. The trade is freshness of
state against the cost of computing it per request.
```

## Notes

- The session boost lifts the audio items' scores (0.032 to 0.041, 0.030 to 0.039) and holds the rest.
- The batch model would need a retrain to learn what the session knows from one dwell; the trade is freshness against per-request cost.
