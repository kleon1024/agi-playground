# Run — the cost-quality pairing, read from the recorded outcome report

**Date:** 2026-08-06
**Command:** `uv run python core/cost_quality.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded report).
**Cost:** \$0 (local lane).

## Purpose

Stage 03's verdict pairs quality with cost. This run reads the recorded
report and lays out the two halves.

## Output

```
  margin (baseline - mean): 0.0430
  margin > spread (0.0430 > 0.0078) -> beats baseline outside seed noise
  ceiling 1800s (not exceeded, 8.4-8.6% used)
  VERDICT: MET
```

## Notes

- The verdict pairs cost with quality rather than reporting either alone —
  mission.yaml's cost/quality-together rule.
- The headroom (8.5% of the ceiling) is the finding: video is affordable
  at this scale before the cost question binds.
