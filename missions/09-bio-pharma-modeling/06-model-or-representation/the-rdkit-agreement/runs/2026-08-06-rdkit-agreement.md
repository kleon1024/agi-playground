# Run — the RDKit agreement, read from the recorded fingerprint check

**Date:** 2026-08-06
**Command:** `uv run python core/rdkit_agreement.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the check was the stage's recorded run).

## Purpose

Stage 06's from-scratch fingerprint was checked against RDKit's. This run
reads the agreement JSON and lays out how close the reimplementation is.

## Output

```
  60 molecules, 1770 pairs, 0 unparsed
  mean bits set: core 47.35 vs RDKit 42.97
  identical bit sets: 0
  Tanimoto Spearman: 0.9012
  mean |Tanimoto diff|: 0.0171
```

## Notes

- The from-scratch fingerprint ranks molecules almost identically to
  RDKit (Spearman 0.90) with tiny mean Tanimoto difference.
- Close enough that the representation comparison's conclusions are not
  an artifact of a broken reimplementation.
