# Serving engine benchmark — 88M chat checkpoint on one 4090

> **Superseded by
> [`2026-07-29-engine-bench-corrected.md`](2026-07-29-engine-bench-corrected.md).**
> The engine measured here had a causal-masking bug: every decode step in both
> cached engines attended only to position 0. That made the cached paths both
> wrong and *faster* than they should have been, so every `KV cache` and
> `paged + continuous` number below is optimistic — increasingly so at longer
> sequences. The `naive` column is unaffected. Kept unedited as the record of
> what was actually run.

## Command

```bash
cd missions/01-language-model-agent/05-serve/core
python engine.py bench --checkpoint ../../03-sft/ckpt/ckpt.pt \
    --prompt-len 64 --max-new-tokens <N> --num-requests <R>
```

Swept twice: `N` over 32/64/128/256/512 at `R=8`, then `R` over 1/2/4/8/16 at
`N=128`.

## Base model

The chat checkpoint from [stage 03](../../03-sft/), which is stage 02's
88,197,888-parameter decoder after supervised fine-tuning. Serving does not
change weights, so the numbers below describe the engine, not the model.

## Hardware and software

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, driver 591.86 |
| Host | WSL2 on Windows, reached over Tailscale |
| Repository | commit `b3bce17` |
| torch | 2.13.0+cu130 |
| Cost | \$0 (local lane) |

Greedy decoding, bf16, no `torch.compile`, no CUDA graphs.

## Result 1: generation length

Single request for the first two engines; `paged + continuous` ran 8.

| New tokens | naive tok/s | KV cache tok/s | speedup | naive peak | KV cache peak |
|---:|---:|---:|---:|---:|---:|
| 32 | 99.6 | 121.2 | 1.22x | 375.1MB | 392.0MB |
| 64 | 120.3 | 144.2 | 1.20x | 380.5MB | 393.0MB |
| 128 | 123.7 | 134.7 | 1.09x | 391.9MB | 395.6MB |
| 256 | 123.1 | 145.1 | 1.18x | 418.0MB | 404.0MB |
| 512 | 130.8 | 140.7 | 1.08x | 483.5MB | 433.5MB |

**The speedup does not grow with sequence length, and that is the finding.**
Recomputing the whole prefix every step is asymptotically quadratic, so theory
says the gap should widen as generation gets longer. It does not. Both engines
sit near a flat 120-145 tokens/second regardless of how much work the naive one
is redoing, which is the signature of a *fixed per-step cost* that dominates
everything else.

At 88M parameters with a batch of one, each decode step is a few dozen small
kernel launches over weights that must be read from memory whatever the
sequence length. The attention arithmetic the KV cache eliminates is small
against that fixed cost until sequences are far longer than 512 tokens. This is
the same effect stage 02 measured from the other side, where `torch.compile`
bought **1.76x** by fusing memory-bound elementwise work and removing launch
overhead.

The memory columns do cross over as expected: past 256 new tokens the naive
path's peak exceeds the cached one, because it re-materialises activations for
the entire sequence on every step while the cache holds only keys and values.

## Result 2: concurrency

`paged + continuous`, 128 new tokens per request, 64-token prompts.

| Concurrent requests | aggregate tok/s | wall-clock | peak memory |
|---:|---:|---:|---:|
| 1 | 118.8 | 1.077s | 376.9MB |
| 2 | 121.4 | 2.108s | 387.0MB |
| 4 | 120.9 | 4.235s | 396.6MB |
| 8 | 121.0 | 8.460s | 417.3MB |
| 16 | 124.5 | 16.450s | 459.1MB |

**Aggregate throughput is flat and wall-clock is linear in the request count.**
Sixteen concurrent requests finish in 15.3x the time one takes. Concurrency
buys exactly nothing here.

This is not a bug, and it is the most useful number in this record.
`ContinuousBatchingEngine.step()` loops over running requests in Python and
issues one forward pass per request per tick — a limitation its own docstring
states. Everything that makes continuous batching *scheduling* is real and
working: blocks are allocated and freed, requests are admitted when memory
allows, finished requests are evicted mid-flight instead of holding a slot. But
the throughput win of batching comes from **one kernel serving many sequences**,
amortising that fixed per-step cost across all of them. With a per-request loop
there is nothing to amortise.

So continuous batching is two separable things, and this run separates them:

- a **scheduling policy** — admit, evict, and free at token boundaries;
- a **fused kernel** over ragged sequence lengths.

The policy is what this lesson implements and can teach. The kernel is what
makes the policy pay, and it is why `prod/vllm_serve.py` exists.

Memory does behave as designed: the paged allocator grows from 376.9MB to
459.1MB across 16x the requests, roughly 5MB per additional concurrent
sequence, because pages are handed out on demand rather than reserved per
request at maximum length.

## What this run does not establish

- **That the KV cache is not worth it.** It establishes that its benefit is
  invisible below ~512 generated tokens at batch 1 on this hardware. The
  asymptotics are real; this scale does not reach them.
- **Anything about latency percentiles.** Every measurement here is aggregate
  throughput on a synthetic prompt of `range(prompt_len)`. No time-to-first-token,
  no inter-token latency distribution, no queueing under load.
- **That a fused kernel would fix the concurrency result.** That is the
  explanation and it is well supported, but this repository has not measured
  `prod/vllm_serve.py` on the same checkpoint to prove it. Until it does, the
  claim is attribution, not evidence.
- **Anything about quality.** Greedy decoding of `range(64)` as a prompt
  produces token sequences, not answers.

## Notes

- Peak memory never exceeded 531.4MB against 24,564MB available, so no
  configuration here was memory-constrained. The paged allocator's admission
  control was never exercised under pressure.
- Both non-batched engines were measured with a single request, so their
  tokens/second is per-request; `paged + continuous` reports the aggregate
  across its concurrent requests. Comparing the two columns directly is only
  meaningful because the aggregate turns out to be flat.
