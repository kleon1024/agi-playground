---
status: draft
---

# 06 — Inference

## Scope

Two related subjects taught together: serving a trained model efficiently
(KV cache, paged attention, continuous batching, speculative decoding,
quantization) and the training-side infrastructure that scales beyond one GPU
(FSDP2, profiling). Both are taught as exercise-driven subjects — the research
found this space is otherwise only taught by "go read vLLM source."

## Prerequisites

`03-pretraining` (needs a trained checkpoint to serve, or profile training
for). Can be entered independently with any small open HF checkpoint if
you're not running the full track sequence.

## Planned lessons

1. `01-kv-cache` — why autoregressive decoding is memory-bound, KV cache from
   scratch.
2. `02-paged-attention` — paged KV blocks, the memory-management idea behind
   vLLM's core innovation.
3. `03-continuous-batching` — dynamic batching across in-flight requests,
   benchmarked against naive `generate()`.
4. `04-speculative-decoding` — draft-and-verify decoding (EAGLE-3-style),
   now default-on in production serving.
5. `05-quantization` — post-training quantization trade-offs for serving.
6. `06-fsdp2-distributed-training` — sharded data parallelism (DTensor-based),
   the 2-8 GPU default.
7. `07-profiling` — PyTorch Profiler → Nsight, finding real bottlenecks.

## Speedrun note

`01-kv-cache` through `03-continuous-batching` are the seed lessons for
speedrun stage `05-serve` (minimal paged-KV inference engine, benchmarked
against naive generation).
