---
status: draft
level: reference
---

# Inference: Landscape

Source: `reference/research/synthesis.md` anchor table, "Inference" and "Training
infra" rows.

| Toy (teach-from) | Production | Our take |
|---|---|---|
| nano-vLLM (~1.2k lines: paged KV, scheduling, prefix cache) | vLLM (see "Anatomy of vLLM"), SGLang, NVIDIA Dynamo (prefill/decode disaggregation) | nano-vLLM is small enough to read in a sitting and implements the real core ideas (paging, scheduling). vLLM and SGLang are the two dominant open serving engines with different design centers (vLLM's PagedAttention lineage vs SGLang's structured-generation focus); Dynamo represents the disaggregated prefill/decode pattern that's becoming the dominant production serving architecture — worth knowing conceptually even though it's out of reach at single-GPU scale. |
| Single-GPU training basics: gradient accumulation, activation checkpointing, mixed precision; PyTorch Profiler → Nsight profiling labs | FSDP2 (DTensor-based sharding), DeepSpeed (MoE/offload cases), tensor/pipeline parallelism on Modal's 2-4 GPU lane | The single-GPU techniques are load-bearing on the single-GPU lane and are exactly what FSDP2 composes across GPUs — read the mechanics locally, then read FSDP2's DTensor abstraction as the same ideas made distributed. DeepSpeed remains relevant for MoE and CPU/NVMe offload cases FSDP2 doesn't target as directly. |

**Single-vendor-rot note:** the inference row names three independent serving
projects; the training-infra row names two distributed-training frameworks
plus a Modal-hosted multi-GPU parallelism lab, so no single project anchors
the track.
