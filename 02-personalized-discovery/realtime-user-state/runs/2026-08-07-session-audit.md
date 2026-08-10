# Run — the depth-stratified session-lift audit over the emitted cohorts

**Commands:** `uv run python core/session_state.py --emit-log /tmp/session-envelope.json`;
`uv run python prod/session_audit.py /tmp/session-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 48's read shows the session re-ranking a slate. This run is the
case-finding half of the stage: the realtime lift that is real in the
aggregate and uneven underneath. The core script emits per-depth cohort
rows; the production audit stratifies the lift by depth and traffic
share, the way a serving team sizes realtime feature spend from logged
sessions instead of from the blended average.

## Output

```
session-lift audit (served CTR by session depth):
  depth signal q  traffic   batch  realtime    lift  share of lift
      0     0.00       0%  0.0090 0.0090 +0.0000            0%
      1     0.50      70%  0.0090 0.0156 +0.0066           58%
      2     0.85      20%  0.0090 0.0196 +0.0106           27%
      4     0.95      10%  0.0090 0.0208 +0.0118           15%

traffic-weighted lift: +0.0079; deep-session (depth 4) lift: +0.0118; single-dwell (depth 1) lift: +0.0066
verdict: SHALLOW SESSION -- the single-dwell sessions that own
70% of traffic earn 56% of the deep-session lift per
session. The blended lift is what the cost model sees, but the
realtime cost is paid per request for every session, so deep
sessions earn the better ROI. Stratify by depth before sizing
the realtime feature spend, and gate the boost on a second
signal for depth-1 sessions.
```

## Notes

- The depth-1 sessions are 70% of traffic and earn 58% of the blended
  lift, but only +0.0066 per session against +0.0118 at depth 4: the
  weakest signal owns the most traffic, so the blend sits near the
  shallow number, not the deep one.
- The audit's message is the stage's: the boost is a function of depth,
  and sizing the realtime spend against the blended lift hides a nearly
  2x per-session ROI difference between shallow and deep sessions.
  Session-state models (Hidasi et al., ICLR 2016) exploit exactly this
  signal; the audit makes its quality measurable.
