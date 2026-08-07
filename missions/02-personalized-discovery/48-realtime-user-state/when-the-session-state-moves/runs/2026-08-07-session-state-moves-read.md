# Run — when the session state moves, executed on the boost-decay read

**Date:** 2026-08-07
**Command:** `uv run python core/session_moves.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.05s.
**Cost:** \$0 (local lane).

## Purpose

Stage 48's detour: the realtime boost for a viewed category decays as the
view recedes. This run reads the slate order at three ages of the view.

## Output

```
session state moves, read (boost on audio, decays per minute):
   2 min since view: boost 0.0097, order ['P1001', 'P1002', 'P1003', 'P1004', 'P1005']
  20 min since view: boost 0.0015, order ['P1001', 'P1003', 'P1002', 'P1004', 'P1005']
  40 min since view: boost 0.0002, order ['P1001', 'P1003', 'P1004', 'P1002', 'P1005']

reading: two minutes after the view the second audio item
outranks the cable item on the session boost; by twenty
minutes the boost has decayed and the batch order is back.
The session state is not binary - its age is the feature -
and the decay curve is where the freshness-versus-stability
decision lives.
```

## Notes

- Two minutes after the view the boost reorders the slate; by twenty minutes the batch order is back.
- The session state is not binary — its age is the feature, and the decay curve is where the freshness-versus-stability decision lives.
