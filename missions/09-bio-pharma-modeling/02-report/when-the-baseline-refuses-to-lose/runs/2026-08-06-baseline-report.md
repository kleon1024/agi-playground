# Run — the SR-MMP verdict, read from the outcome report

**Date:** 2026-08-06
**Command:** `uv run python core/baseline_report.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.01s (tabulates the recorded report).
**Cost:** \$0 (local lane).

## Purpose

Mission 09's report compared the descriptor baseline against the trained
SMILES model on the scaffold-checked split. This run tabulates the recorded
means and spreads and reads the verdict structure.

## Output

```
descriptor baseline: 0.8142 +- 0.0010
trained model:       0.7312 +- 0.0159
gap (descriptor - model): +0.0830 vs larger spread 0.0159
-> model beats baseline: False
```

## Notes

- The gap (0.083) is 5x the larger spread (0.016): the baseline wins
  decisively, not a near-tie. The model is clearly worse on this endpoint.
- The scaffold-checked split means the win is not a leakage artifact: the
  held-out structures were not in training, so the baseline's edge is real
  generalization, which is the honest reading of "the baseline refused to
  lose."
