# Run — two ways to read a molecule, read from the recorded runs

**Date:** 2026-08-06
**Command:** `uv run python core/representation_anatomy.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads six committed seed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-01
runs).

## Purpose

The bio-pharma "model" is two representations of the same molecule. This
run reads the recorded runs and lays out the two structures side by side.

## Output

```
two representations of one molecule, read from the recorded runs:
  descriptor:  10 RDKit numbers -> logistic regression
               mean ROC-AUC 0.8142, spread 0.0010, ~2s/seed
  SMILES model: character transformer, 696,065 params, vocab 52
               mean ROC-AUC 0.7312, spread 0.0159, ~105s/seed
```

## Notes

- The descriptor's edge on SR-MMP is partly that it is a stable, cheap
  ten-number summary: ~2s per seed, spread 0.0010.
- The transformer's variance (spread 0.0159, ~105s/seed) is where the
  mission's scarcity story begins — the same confound stages 03-05 chase.
