# Run — the feasibility frontier: four grid corners, assembled

**Date:** 2026-08-06
**Command:** `uv run python core/frontier_grid.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads four recorded JSONs).
**Cost:** \$0 (local lane; the underlying training was the stages' recorded
runs).

## Purpose

The mission's generation stages sample a frames x objects grid. This run
assembles the four corners' reconstruction MSE from the recorded runs, so
the frontier — which axis costs more — is one table.

## Output

```
corner                     lm MSE  frame-repeat
8 frames x 1 object        0.0804        0.1281
16 frames x 1 object       0.0818        0.1185
8 frames x 2 objects       0.1429        0.2193
16 frames x 2 objects      0.1391        0.1998
```

## Notes

- Objects are the dominant axis: 1 -> 2 objects roughly doubles both MSEs
  (lm 0.080 -> 0.143), while frames 8 -> 16 move it almost not at all
  (0.0804 -> 0.0818 at one object). The multi-object corner's cost is
  occlusion and interaction, not length.
- The LM beats frame-repeat at every corner (MET throughout): feasibility
  holds on the whole grid, and the 16x2 corner's exact-match 0.00% (recorded)
  is the token metric at zero while the pixel metric still holds — the
  wrong-tokens lesson at the frontier.
