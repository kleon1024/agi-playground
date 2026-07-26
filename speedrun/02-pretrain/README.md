---
status: draft
---

# Speedrun 02 — Pretrain

## Goal

Train a small GPT-class decoder from scratch on the tokenized speedrun
corpus, entirely on the single-GPU lane.

## Deliverable

An ~88M-parameter decoder (RMSNorm, RoPE, SwiGLU, GQA), trained bf16 with
gradient accumulation, hours-scale wall-clock, with a published loss curve.

## Anchor project

nanoGPT/nanochat (see `tracks/03-pretraining/LANDSCAPE.md` for the
toy/production mapping). Seed lessons: `tracks/03-pretraining/README.md`,
`02-gpt-architecture` and `03-training-loop` — built on `tracks/01-foundations`
(tensors, autograd, attention, transformer block).

## Verification criterion

No verified run yet — depends on `00-corpus` and `01-tokenizer` landing
first. When trained, its `runs/` entry must show: the exact training command
and config (architecture dims, batch size, grad-accum steps, learning-rate
schedule), hardware, wall-clock time, and a Trackio-exported loss
curve — not a single final-loss number.
