# Run — the LSH duplicate-threshold S-curve, measured

**Date:** 2026-08-07
**Command:** `uv run python core/release_policy.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 9s (600 trials x 5 Jaccard levels x 2 band configs).
**Cost:** \$0 (local lane).

## Purpose

The release-policy chapter's S-curve table is computed from the band and
row counts. This run measures the same curve empirically: random
shingle-set pairs at declared Jaccard levels, 64-permutation MinHash
signatures, and the fraction of pairs where any band matches, against the
analytic formula 1 - (1 - J^4)^16, plus the shifted curve for 32 bands of
4 rows (128 permutations).

## Output

```
release policy, measured (LSH duplicate-threshold S-curve):
  trials 600 per Jaccard level, shingle-set size 48, 64-permutation signatures
      J  16x4 measured 16x4 formula 32x4 measured 32x4 formula
    0.1          0.002        0.002         0.000        0.003
    0.3          0.095        0.122         0.233        0.229
    0.5          0.680        0.644         0.873        0.873
    0.7          0.987        0.988         1.000        1.000
    0.9          1.000        1.000         1.000        1.000

  implied threshold: 16 bands of 4 rows -> 0.50; 32 bands of 4 rows -> 0.42
```

## Notes

- The measured 16x4 curve tracks the formula across the whole S-shape:
  0.002 vs 0.002 at J=0.1, 0.095 vs 0.122 at J=0.3, 0.680 vs 0.644 at
  J=0.5, 0.987 vs 0.988 at J=0.7, 1.000 vs 1.000 at J=0.9. The chapter's
  computed table is now a measured property of the band settings.
- The 32x4 config is the release-policy example in action: the implied
  threshold moves from 0.50 to 0.42, and the measured curve shifts with
  it (0.233 vs 0.229 at J=0.3, 0.873 vs 0.873 at J=0.5). Raising the band
  count lowers the duplicate threshold whether or not it was intended.
- At J=0.1 the candidate rate is 0.002-0.003 (2-3 pairs per thousand),
  which is the false-positive load the verification pass has to absorb.

## Evidence boundary

Synthetic shingle sets at declared Jaccard levels (deterministic, single
seed, 600 trials per level). It verifies the threshold curve and its
shift; real duplication rates and candidate loads come from the corpus's
actual document population.
