# vLLM against the hand-written engine — same checkpoint, same sweep

## Why this run exists

[`2026-07-28-engine-bench.md`](2026-07-28-engine-bench.md) measured the
hand-written engine at a flat 118.8-124.5 aggregate tokens/second from 1 to 16
concurrent requests, and blamed the missing fused kernel. That record says
plainly that the blame was **attribution, not evidence**, because no engine
with a fused kernel had been measured on the same checkpoint.

This is that measurement. Every parameter is held identical to the earlier
sweep: the same weights, the same 64-token prompt of `range(64)`, 128 new
tokens per request, greedy decoding, request counts 1/2/4/8/16.

## Command

```bash
cd 01-language-model/05-serve/prod
python vllm_serve.py convert ~/agi-playground/stage03/ckpt/ckpt.pt ~/hf-88m-sft
python vllm_serve.py bench ~/hf-88m-sft \
    --prompt-len 64 --max-new-tokens 128 --requests 1 2 4 8 16 [--eager]
```

Run twice: once with CUDA graphs enabled (vLLM's default) and once with
`--eager`, which keeps the fused kernels and removes the graphs.

## What was deliberately switched off

- **Prefix caching.** All 16 requests send the identical prompt, so vLLM would
  serve 15 of 16 prefills from cache. That is a real feature and a completely
  different effect; the hand-written engine has no such cache, and crediting
  the kernel for a saving the kernel did not make would corrupt the comparison.
- **The tokenizer** (`skip_tokenizer_init=True`). Token ids in, token ids out,
  exactly as in `core/engine.py`, so detokenization is outside both intervals.
- **EOS** (`ignore_eos=True`). Every request emits exactly 128 tokens, matching
  the core engine's unconditional loop.

## Hardware and software

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4090, 24,564 MiB, driver 591.86 |
| Host | WSL2 on Windows, reached over Tailscale |
| vLLM | 0.26.0, torch 2.11.0+cu130, separate venv from the training environment |
| Model | the stage-03 chat checkpoint, converted to `LlamaForCausalLM` naming |
| Cost | \$0 (local lane) |

vLLM reported 13.71 GiB of KV cache after loading the 88M model, or 1,152,061
tokens — enough for 5,760 concurrent requests at this sequence length. Nothing
in this sweep came close to a memory limit.

## Result

| Concurrent requests | 1 | 2 | 4 | 8 | 16 |
|---|---:|---:|---:|---:|---:|
| Hand-written engine, aggregate tok/s | 118.8 | 121.4 | 120.9 | 121.0 | 124.5 |
| vLLM eager, aggregate tok/s | 178.3 | 336.0 | 667.0 | 1310.5 | 2488.2 |
| vLLM with CUDA graphs, aggregate tok/s | 836.1 | 1632.6 | 3138.5 | 5589.7 | 11093.0 |
| Hand-written engine, wall-clock | 1.077s | 2.108s | 4.235s | 8.460s | 16.450s |
| vLLM eager, wall-clock | 0.718s | 0.762s | 0.768s | 0.781s | 0.823s |
| vLLM with CUDA graphs, wall-clock | 0.153s | 0.157s | 0.163s | 0.183s | 0.185s |

**The attribution was correct, and the run separates two effects that were
previously bundled together.**

**Batching.** vLLM eager keeps the fused, batched attention kernel and throws
away the CUDA graphs. Going from 1 to 16 concurrent requests multiplies
throughput by **14.0x** while wall-clock rises only 1.15x. The hand-written
engine, given the identical scheduling decisions, managed 1.05x throughput and
15.3x wall-clock. That gap is the whole content of the earlier record's claim:
the scheduler was never the problem.

**Launch overhead.** CUDA graphs multiply throughput by **4.7x at one request**
and 4.5x at sixteen — almost exactly flat across the sweep. A constant factor
across all concurrencies is the signature of a per-step cost that does not
depend on how much work the step contains, which is what kernel launch overhead
is. This is the same effect stage 02 measured from the training side, where
`torch.compile` bought 1.76x.

The two compose to **89x** at 16 concurrent requests.

**At a single request**, where there is nothing to batch, vLLM eager is still
1.5x the hand-written engine. That residual is the fused attention kernel
itself against `core/engine.py`'s eager PyTorch, with no scheduling involved.

## What this run does not establish

- **That the hand-written engine is badly written.** It implements the
  scheduling policy it claims to implement, and this run confirms the policy is
  the correct one — running it through a fused kernel is what pays. The gap is
  a missing kernel, not a missing idea.
- **Anything about latency percentiles.** Aggregate throughput on a synthetic
  prompt again. No time-to-first-token, no inter-token distribution, no
  behaviour under sustained arrival rates.
- **That these numbers transfer to a serving-sized model.** At 88M parameters
  the fixed per-step cost dominates, which is exactly why CUDA graphs are worth
  4.7x here. On a 7B model the same graphs typically buy far less, because the
  GEMMs are large enough to hide the launches. Reading this table as a general
  statement about vLLM would be a scale error.
- **Anything about quality.** Greedy decoding of `range(64)` produces token
  sequences, not answers.

## Notes

- vLLM 0.26.0 would not start on this host until three things were resolved,
  all of them environment rather than model: WSL2 has no UVA, so the V2 model
  runner fails at `RuntimeError: UVA is not available` and
  `VLLM_USE_V2_MODEL_RUNNER=0` is required; the JIT path needs `nvcc`, supplied
  by pointing `CUDA_HOME` at the `nvidia/cu13` wheel inside the venv, plus
  `ninja`; and FlashInfer's bundled CCCL headers are incompatible with that
  `nvcc`, so `VLLM_USE_FLASHINFER_SAMPLER=0` avoids compiling a sampler that
  greedy decoding does not need.
- vLLM was installed into its own virtual environment. The training environment
  pins torch 2.13.0+cu130 and every earlier run in this repository was recorded
  against it; letting a vLLM install move that pin would have silently
  invalidated the comparison this record depends on.
- Engine startup, including compilation and graph capture, took 14.6 seconds
  and is outside the measured interval. One warm-up request runs before timing
  begins.
