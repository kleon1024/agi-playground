---
status: draft
---

# 03 — Pretraining

## Scope

Turning a cleaned corpus into a trained decoder-only language model: your own
BPE tokenizer, a GPT-style architecture (RMSNorm, RoPE, SwiGLU), the training
loop (bf16, gradient accumulation, checkpointing), and enough scaling-law
intuition to reason about model/data/compute trade-offs at toy scale. This
track is where `01-foundations`' mechanics and `02-data`'s corpus meet.

## Prerequisites

`01-foundations` (tensors, autograd, attention, transformer block) and
`02-data` (a cleaned, deduplicated shard to tokenize and train on — or use the
speedrun's published shard directly).

## Planned lessons

1. `01-bpe-tokenizer-from-scratch` — byte-pair encoding, minbpe-style, trained
   on a real shard.
2. `02-gpt-architecture` — RMSNorm, RoPE, SwiGLU, assembling the modern
   GPT-class decoder (nanoGPT/nanochat-style).
3. `03-training-loop` — bf16 mixed precision, gradient accumulation,
   checkpointing, an hours-scale run with a published loss curve.
4. `04-scaling-laws-and-ablations` — reading loss curves, model/data/compute
   trade-offs, small ablations at single-GPU scale.
5. `05-mapping-to-production-trainers` — reading torchtitan/nanotron/OLMo-core
   configs against the from-scratch training loop.

## Speedrun note

`01-bpe-tokenizer-from-scratch` is the seed lesson for speedrun stage
`01-tokenizer` (own BPE, 8-16k vocab, trained on the speedrun shard).
`02-gpt-architecture` and `03-training-loop` are the seed lessons for speedrun
stage `02-pretrain` (~120M-class decoder, hours-scale run, published loss
curve).
