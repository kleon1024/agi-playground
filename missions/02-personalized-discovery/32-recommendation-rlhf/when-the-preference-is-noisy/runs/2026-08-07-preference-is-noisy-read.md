# Run — when the preference is noisy, executed on the flipped-label loss read

**Date:** 2026-08-07
**Command:** `uv run python core/noisy_preference.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 32 optimizes a ranker from pairwise preferences. This run flips one of three labels and reads the loss floor the clean pairs cannot remove.

## Output

```
noisy preference, read (1 of 3 labels flipped):
  chosen 1.2 vs rejected 0.4: loss 0.00
  chosen 0.9 vs rejected 0.8: loss 0.09
  chosen 0.3 vs rejected 1.1: loss 0.80 (flipped)
  total loss floor: 0.89

reading: the flipped pair pushes the model the wrong way and
sets a loss floor the clean pairs cannot remove. Real RLHF
labels are noisy, so the pipeline has to filter or reweight —
the frontier cost is label quality, not model capacity.
```

## Notes

- The flipped pair (0.3 vs 1.1) forces a wrong gradient and sets a 0.80 loss; the total floor is 0.89.
- Real RLHF labels are noisy, so the pipeline has to filter or reweight — the frontier cost is label quality, not model capacity.
