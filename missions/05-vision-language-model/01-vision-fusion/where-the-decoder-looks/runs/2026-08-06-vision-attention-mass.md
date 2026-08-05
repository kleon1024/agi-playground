# Run — attention mass on the vision prefix, by question type

**Date:** 2026-08-06
**Command:** `cd missions/05-vision-language-model/01-vision-fusion/where-the-decoder-looks && uv run --group torch python core/vision_attention_mass.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; torch 2.13.0; reuses the stage's
`train.py` and `vlm_model.py` unmodified.
**Wall-clock:** ~4.5 minutes (retrain seed 0, 30 epochs, then 784 eval
forwards).
**Cost:** \$0 (local lane).

## Purpose

The recorded accuracy separates the vision pathway on color questions (50.1%
versus 27.2% for text-only). The naive mechanism to explain that is "the
decoder attends more to the image when the question needs it." This run
measures that claim at the last fusion layer, split by question type, using
the diagnostic `forward_capturing_attention` (never on the training path).

## Metrics

```
mean attention mass on the 64 vision tokens, layer 3, by question type:
  color          n= 261  mean vision mass=0.01029  half-range=0.00299
  other          n= 523  mean vision mass=0.01226  half-range=0.00412
  ratio color/other = 0.84x
```

## Notes

- The hypothesis fails: the decoder spends *less* mean attention mass on the
  vision prefix for color questions (0.0103 vs 0.0123), not more. The
  separation the accuracy shows is real (recorded), and attention mass does
  not explain it.
- The absolute mass is tiny (~1% of a text query's weight lands on 64 vision
  tokens at layer 3), so the vision signal is not carried by weight
  magnitude at this layer. The plausible carriers: the content of the vision
  value vectors the decoder pulls, or earlier layers, or both.
- This is the attention-is-not-explanation result (Jain & Wallace, 2019),
  measured on this repo's own model: attention weights are a distribution,
  and the information used is what the values contribute, not how much mass
  a prefix receives.
- Layer 3 only, one seed, greedy eval forward; the accuracy numbers cited in
  the chapter are the recorded 3-seed means, not re-measured here.
