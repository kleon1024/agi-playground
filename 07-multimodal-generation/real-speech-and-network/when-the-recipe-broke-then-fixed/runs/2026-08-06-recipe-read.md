# Run — the recipe that broke then fixed on real speech, read from the record

**Date:** 2026-08-06
**Command:** `uv run python core/recipe_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown and JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded runs).

## Purpose

Stage 03's real-speech retrain found the synthetic recipe collapses on
LibriSpeech at 600 steps and escapes at 2000. This run reads the sweep and
the production seeds.

## Output

```
  lr=1e-3 (unchanged): escapes by step ~1400-1800, eval MSE 0.01306, 58/64 codes
  lr=3e-3 (higher):    never escapes, eval MSE 0.02722 (silence tie), 3/64 codes
  seed 0: eval MSE 0.01306, codes 58/64
  seed 1: eval MSE 0.01369, codes 51/64
  seed 2: eval MSE 0.01309, codes 63/64
```

## Notes

- The same LR that escaped synthetic tones collapses on real speech at
  600 steps and escapes by 2000; a higher LR never escapes.
- The recipe's escape window is input-dependent, which is why the
  production run fixed the step count at 2000.
