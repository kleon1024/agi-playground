# Run — realtime user state, executed on the session-boost read

**Date:** 2026-08-07
**Commands:** `uv run python core/session_state.py --emit-log /tmp/session-envelope.json`;
`uv run python prod/session_audit.py /tmp/session-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 48 introduces real-time personalization. This run ranks one slate
with the batch model's learned priors and with a session boost for a user
who dwelled on an audio item, then runs the session-cohort simulation
the audit stratifies by session depth.

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

session cohort view (served CTR, batch vs realtime):
  depth signal q  traffic   batch  realtime   lift
      0     0.00       0%  0.0090 0.0090 +0.0000
      1     0.50      70%  0.0090 0.0156 +0.0066
      2     0.85      20%  0.0090 0.0196 +0.0106
      4     0.95      10%  0.0090 0.0208 +0.0118

  traffic-weighted lift: +0.0079 (deep-session lift +0.0118)

  reading: the boost pays, but the per-session payment
  grows with depth. Depth 1 - a single dwell, the majority
  of sessions - earns about half the deep-session lift, and
  the cost is paid per request for every session. The blend
  hides the ROI difference; stratify before sizing the
  realtime feature spend.
```

## Notes

- The session boost lifts the audio items' scores (0.032 to 0.041, 0.030 to 0.039) and holds the rest.
- The batch model would need a retrain to learn what the session knows from one dwell; the trade is freshness against per-request cost.
- The cohort simulation stratifies served CTR by session depth: the
  single-dwell sessions (70% of traffic) earn +0.0066 against the
  deep-session +0.0118, so the traffic-weighted lift (+0.0079) sits
  closer to the shallow number. The audit reads the emitted envelope
  and returns the SHALLOW SESSION verdict: the blended number is what
  the cost model sees, but the realtime cost is paid per request for
  every session.
