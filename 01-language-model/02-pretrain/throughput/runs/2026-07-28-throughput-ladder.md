# Throughput ladder on the 88M configuration — one 4090

## Command

```bash
cd 01-language-model/02-pretrain/throughput/core
python throughput.py ladder --micro-batch 16 --steps 30 --warmup 10 --out ladder.json

cd ../prod
python profile_step.py --no-compile --rows 8
python profile_step.py --compile --rows 8
```

Each rung runs in its own process. Thirty timed steps follow ten discarded
warm-up steps, which absorb cuDNN autotuning, allocator growth, and — on the
compiled rung — the entire compilation.

## Model and hardware

The stage-02 pretraining configuration exactly: 88,197,888 parameters, 12
layers, `d_model` 768, 12 query heads over 4 KV heads, 1,024-token sequences,
micro-batch 16. Synthetic random token batches, so this measures the loop and
not the data pipeline.

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, driver 591.86 |
| Host | WSL2 on Windows, reached over Tailscale |
| torch | 2.13.0+cu130 |
| MFU denominator | 165 TFLOP/s, bf16 dense |
| Cost | \$0 (local lane) |

## Result: the ladder

| Configuration | tok/s | MFU | step | peak memory | cumulative |
|---|---:|---:|---:|---:|---:|
| fp32 eager, math attention | 11,521 | 4.5% | 1422.1ms | 27,708.7MB | 1.00x |
| + bf16 autocast | 32,463 | 12.6% | 504.7ms | 23,565.1MB | 2.82x |
| + flash attention | 95,328 | 37.1% | 171.9ms | 13,303.1MB | 8.27x |
| + fused AdamW | 98,246 | 38.3% | 166.8ms | 13,303.2MB | 8.53x |
| + `torch.compile` | 169,230 | 65.9% | 96.8ms | 8,685.7MB | 14.69x |
| + activation checkpointing | 140,748 | 54.8% | 116.4ms | 3,410.4MB | 12.22x |

Five flags, **14.69x**, and MFU from 4.5% to 65.9% with the model, the batch,
and the card unchanged.

The `torch.compile` rung independently reproduces stage 02's measurement. That
run recorded 165.6k tokens/second at 64.5% MFU on the same configuration
against 85.5k uncompiled; this ladder gets 169.2k at 65.9% against 98.2k. The
two agree to within 2% on the compiled figure, from different code, weeks
apart.

## The first rung is contaminated, and here is the control

**fp32 at micro-batch 16 needs 27.7GB on a 24.5GB card.** It did not fail,
because WSL2's driver silently pages GPU allocations into host memory rather
than raising out-of-memory. So the 2.82x credited to bf16 above is partly bf16
arithmetic and partly PCIe traffic, and the table cannot separate them.

Rerun at micro-batch 4, where both dtypes fit in VRAM with room to spare:

| micro-batch 4, math attention | tok/s | MFU | peak memory |
|---|---:|---:|---:|
| fp32 | 30,611 | 11.9% | 7,739.4MB |
| bf16 | 39,183 | 15.3% | 6,849.3MB |

**1.28x, not 2.82x.** The honest reading of the ladder is that bf16 is worth
roughly 1.3x directly, and worth a great deal more indirectly, because halving
the activation footprint is what keeps micro-batch 16 resident at all. The
larger figure is real as a wall-clock outcome and wrong as an attribution.

This is the most useful thing in this record. A card that pages instead of
failing will happily produce a plausible number for a configuration that does
not fit, and nothing in the output says so.

## Where the time goes

`prod/profile_step.py`, five steps, self-CUDA time.

| | eager | compiled |
|---|---:|---:|
| Total self-CUDA | 818.577ms | 477.588ms |
| `aten::mm` | 275.819ms (33.7%) | 277.485ms (58.1%) |
| `aten::mul` | 174.229ms (21.3%) | absorbed into fused kernels |
| `aten::copy_` | 119.998ms (14.7%) | absorbed into fused kernels |

**The matmuls do not move: 275.8ms against 277.5ms.** Compilation removed
341ms of everything else and left the arithmetic exactly where it was. That is
what "memory-bound elementwise work" means as a measurement rather than an
assertion — before compiling, two thirds of the card's time was spent on
operations that produce no FLOPs anyone asked for, and afterwards the same
matmuls account for 58% of a much shorter step.

The compiled profile shows Triton kernels with names like
`triton_poi_fused__unsafe_view_mul_silu_silu_backward` — several separate
elementwise operations emitted as one kernel, which is the mechanism in the
kernel name.

`Command Buffer Full` accounts for 37-38% of host time in both profiles, which
is the CPU blocking because the GPU's launch queue is saturated. Fusion reduces
the number of launches (3,498 to 1,499 in these profiles) without changing that
the host is the one waiting.

## What this run does not establish

- **That these multipliers transfer.** 88M parameters at sequence length 1,024
  is a regime where fixed per-step costs are large relative to the arithmetic.
  A larger model spends proportionally more time in GEMMs, so fusion and launch
  reduction buy less. The ranking is likely stable; the magnitudes are not.
- **That activation checkpointing is a loss.** It costs 17% of throughput and
  returns 2.5x the memory, which is a trade and not a regression. Whether it is
  worth taking depends on whether the memory buys a larger batch — this run did
  not test that, because it held micro-batch fixed to keep the column
  comparable.
- **That fused AdamW does nothing.** It is worth 1.03x here, which at 88M is
  almost noise, because the optimizer touches 88M parameters once per step
  against 16.8M tokens of forward and backward work. The ratio moves toward the
  optimizer as batch size falls.
- **Anything about loss.** Every number here is throughput. No rung was trained
  to convergence and no rung's final quality was measured. bf16 autocast in
  particular changes the numerics, and this record has nothing to say about
  whether it changes the result.

## Notes

- MFU is reported against 165 TFLOP/s. That denominator is a published
  specification, not a measured one, so MFU here is comparable across this
  repository's runs and should not be compared against a number computed with a
  different denominator.
- The FLOPs-per-token estimate is the standard `6 * params + 12 * n_layer *
  block_size * d_model`, which counts the matmuls and the attention term and
  ignores norms, activations, and the optimizer. It understates real work, so
  MFU here is a slight underestimate.
