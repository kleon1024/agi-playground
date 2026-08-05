# Run — the descriptor-vs-model scoreboard, assembled from the recorded runs

**Date:** 2026-08-06
**Command:** `uv run python core/scoreboard.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads 18 recorded JSONs).
**Cost:** \$0 (local lane; the underlying training was the mission's recorded
runs).

## Purpose

The mission README's scoreboard lives across three stage records. This run
assembles the per-endpoint descriptor and model test ROC-AUC (3 seeds each)
into one table, applying the mission's own rule — a margin smaller than the
seed spread is no result — using the larger of the two spreads.

## Output

```
endpoint          descriptor           model         margin   winner
SR-MMP        0.8142±0.0005   0.7312±0.0080   +0.0830   descriptor
NR-PPAR-gamma 0.6554±0.0022   0.6591±0.0310   -0.0037   inside spread
NR-ER         0.6413±0.0005   0.6679±0.0113   -0.0265   model
```

## Notes

- The assembled table reproduces the mission's recorded verdicts exactly:
  descriptor wins on SR-MMP, the PPAR comparison is inside the model's seed
  spread (0.031), and the model wins on NR-ER.
- The pattern is not "the baseline is better"; it is per-endpoint: the
  baseline's win margin is largest where the model's variance is smallest
  (SR-MMP), and the model's win on NR-ER is beyond its own spread.
- The PPAR row's inside-spread verdict connects to the split chapter's
  label shift: the endpoint with the largest scaffold-split shift is the
  one with no winner — the scarcity and the variance are the same confound.
