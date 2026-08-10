# Run — the margin vs the oracle ceiling, read from the recorded runs

**Date:** 2026-08-06
**Command:** `uv run python core/margin_ceiling.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three committed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-07-31
runs).

## Purpose

Stage 02's generation beats frame-repeat and sits near the oracle. This
run reads the JSONs and lays out where the remaining gap lives.

## Output

```
  seed 0: lm 0.0804 oracle 0.0779 frame-repeat 0.1281
  seed 1: lm 0.0865 oracle 0.0865 frame-repeat 0.1281
  seed 2: lm 0.0882 oracle 0.0882 frame-repeat 0.1281
```

## Notes

- The LM beats frame-repeat on every seed and sits close to the oracle.
- The remaining gap is the codec's reconstruction fidelity, not the
  sequence model's.
