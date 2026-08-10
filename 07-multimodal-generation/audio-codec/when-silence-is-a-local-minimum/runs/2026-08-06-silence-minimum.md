# Run — the silence local minimum, read from the recorded codec training run

**Date:** 2026-08-06
**Command:** `uv run python core/silence_minimum.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-07-31
run).

## Purpose

Stage 00's first attempt collapsed to a silence-matching local minimum.
This run reads the record and lays out what the pilot showed and how the
escape worked.

## Output

```
  plateaued at recon MSE 0.325
  codebook usage collapsed to 1-2 of 64 codes
  outputting near-silence is a locally optimal way to minimize MSE
    against a zero-mean signal
  loss drops sharply (0.32 -> 0.03) once the decoder escapes
```

## Notes

- Against a zero-mean signal, silence is locally optimal: the decoder must
  escape a genuine minimum, not just train longer.
- The escape is why the training recipe (higher LR, longer) matters as much
  as the loss function.
