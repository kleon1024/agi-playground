# Run — the width that buys memorization, read from the recorded grid

**Date:** 2026-08-06
**Command:** `uv run python core/width_memorization.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.01s (reads two recorded JSONs).
**Cost:** \$0 (local lane; the underlying training was stage 06's recorded
run).

## Purpose

Stage 06's recorded grid held a bit-width sweep on SR-MMP that the stage
README did not put in the main path. This run lays out that sweep plus the
RDKit agreement, so the "width buys memorization" pattern is measured
instead of buried in the JSON.

## Output

```
bit-width sweep, SR-MMP (recorded 2026-08-05)
  n_bits  train AUC  test AUC     gap  test spread
      64     0.8032    0.6812  0.1220       0.0037
     256     0.9045    0.7135  0.1911       0.0013
    1024     0.9934    0.6732  0.3202       0.0009
    2048     0.9995    0.6534  0.3460       0.0010

RDKit agreement (core fingerprint vs RDKit, n=60 molecules)
  mean bits set: core 47.35 vs rdkit 42.97
  identical bit sets: 0/60
  tanimoto Spearman (core vs rdkit): 0.901
  mean |tanimoto difference|: 0.0171
```

## Notes

- Test AUC peaks at 256 bits (0.7135) and declines beyond (0.673 at 1,024,
  0.653 at 2,048), while train AUC climbs to 0.9995. Width beyond the knee
  buys memorization the scaffold split does not let transfer.
- The memorization gap (train minus test) grows monotonically 0.122 to
  0.346 across the sweep — the clearest single number in the record.
- The core fingerprint agrees with RDKit at rank level (Tanimoto Spearman
  0.901, mean difference 0.017) but is never bit-identical (0/60): it is
  faithful in ordering, not in bits, which the chapter reads as "the
  representation is the field's, the bits are this repo's."
