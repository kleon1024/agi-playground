# Run — stage 02 training loop mechanics

**This is not the pretraining run.** It is a short verification that the loop,
the model, and the data path work together, plus the throughput measurements
needed to size the real run. The real run waits on stage 01's tokenizer.

**Date:** 2026-07-26
**Hardware:** RTX 4090 24GB (driver 591.86), WSL2, torch 2.13.0+cu130.
**Cost:** $0 (local lane). ~40 seconds of GPU time.

## What was run

A 1,024-vocabulary smoke tokenizer (from stage 01's early comparison) over 8,000
FineWeb-Edu documents, then 15 optimizer steps against it:

```bash
python prepare_data.py ../data/fineweb-edu/sample/10BT ../stage01/hf_smoke.json \
  --out-dir /tmp/tok02 --limit-docs 8000 --val-tokens 200000
python train.py --data /tmp/tok02 --out /tmp/ckpt02 --tokens 2.0e6 \
  --eval-every 5 --eval-iters 10
```

Tokenization: 15.1M tokens in 2.3s (**6.6M tok/s**).

## Output

```
TOTAL                                 88,197,888  (88.2M)
KV cache per token:   12,288 bytes (bf16)
  ... under full MHA:  36,864 bytes (3x more)

train tokens 14,908,558 | val tokens 201,544
tokens/step  131,072 (micro 16 x block 1024 x accum 8)

step       0  val 9.8401  lr 1.20e-06     0.0k tok/s  MFU  0.0%
step       5  val 9.6103  lr 7.20e-06    76.7k tok/s  MFU 29.9%
step      10  val 9.0982  lr 1.32e-05    83.1k tok/s  MFU 32.4%
step      15  val 8.8291  lr 1.92e-05    85.5k tok/s  MFU 33.3%

peak VRAM: 13.68 GB
```

## What it establishes

**The initialization check passes.** Step-0 loss of 9.8401 sits just above
`ln(16512) = 9.712`, the uniform-random baseline over the padded vocabulary —
the same check the [foundations lesson](../../../../foundations/01-first-training-loop/)
introduces, now confirming that a very different architecture (RMSNorm, RoPE,
SwiGLU, GQA) with a different vocabulary and a memmapped data path is also wired
correctly. Loss then falls monotonically, so the optimizer, schedule, and
accumulated gradients are doing what they should.

**Throughput and memory are measured, not assumed.** 85.5k tok/s at 33.3% MFU,
without `torch.compile`. Peak allocation 13.68 GB of 24 GB, so there is room to
raise the micro-batch.

**Sizing the real run.** At the measured 85.5k tok/s, the 3.01B-token corpus
takes **≈9.8 hours** — an overnight run. `--compile` should reduce that; the
real run will report what it actually achieved rather than a projection.

## What it does not establish

Nothing about model quality. The tokenizer here has a 1,024-token vocabulary
built for a speed comparison, so the model is predicting over a vocabulary that
fragments text badly, and 15 steps is far too few to mean anything. Loss values
from this run are not comparable to the real one.

## Notes

- The `--compile` path is untested as of this run.
- MFU assumes 165 TFLOP/s bf16 dense for the card. The figure is a ratio against
  that constant; a different card needs `peak_flops` adjusted in `train.py`.
- Padding the vocabulary to 16,512 costs a slightly larger embedding than the
  16,385 strictly needed. That is deliberate — see the comment in `model.py`.
