# Run — the feasibility verdict, quality margin recomputed

**Date:** 2026-08-06
**Command:** `uv run python core/cost_report.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three generation JSONs).
**Cost:** \$0 (local lane; the underlying training was the mission's recorded
runs).

## Purpose

Mission 08's report is the feasibility verdict. This run recomputes the
quality margin from the committed generation JSONs and tabulates the
recorded cost against the ceiling, so the verdict's two halves are one
table.

## Output

```
LM completion per seed: [0.0804, 0.0865, 0.0882]
mean 0.0851, spread 0.0078, frame-repeat 0.1281
margin 0.0430 > spread 0.0078 -> beats baseline outside seed noise

  cost half (recorded):
  seed totals 152.5/150.6/153.9s (codec + LM + generation), $0,
  ceiling 1800s -> 8.4-8.6% used
```

## Notes

- The quality margin (0.0430) is 5.5x the seed spread (0.0078) — beats
  frame-repeat decisively. The exact-token match is low (0.07-0.22) but the
  wrong-tokens lesson says the pixel metric is the one the verdict rests on.
- The cost ceiling is roomy: 8.4-8.6% of the declared 1800s. The verdict
  pairs cost with quality (per mission.yaml's discipline), and the headroom
  is the finding — video is affordable at this scale before the cost
  question binds.
- The failure catalogue (3 sequential training collapses before the working
  codec) is the other half of the report's honesty: the verdict documents
  the path, not just the destination.
