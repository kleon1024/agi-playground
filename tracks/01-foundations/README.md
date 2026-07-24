---
status: draft
---

# 01 — Foundations

## Scope

The substrate every later track assumes: tensors and their operations, autograd
built from scratch, attention mechanics, and the transformer block that
composes them. No ML background is required beyond this track — just Python
and basic math (linear algebra, calculus, probability at an undergraduate
level). Everything here is small enough to run on a laptop CPU; the GPU lane
isn't needed until 03-pretraining.

This track has no `LANDSCAPE.md` production row of its own in
`research/synthesis.md` — it's prerequisite scaffolding, not a taught
toy-vs-production pairing. Its `LANDSCAPE.md` instead lists the general-purpose
libraries these mechanics map onto once you leave the from-scratch code.

## Prerequisites

None. This is the entry point. Software engineering fluency (any language) and
comfort with matrix/vector notation and derivatives are assumed; no prior ML
exposure is required.

## Planned lessons

1. `01-tensors-and-ops` — tensors as nested arrays, broadcasting, basic ops,
   why frameworks vectorize.
2. `02-autograd-from-scratch` — a minimal reverse-mode autodiff engine
   (scalar and small-tensor), the mechanics PyTorch's `autograd` automates.
3. `03-attention-mechanics` — scaled dot-product attention derived from first
   principles, multi-head splitting, causal masking.
4. `04-transformer-block` — layer norm/RMSNorm, residual streams, MLP/SwiGLU,
   assembling a full decoder block.
5. `05-mini-gpt-forward-pass` — wiring the block into a tiny GPT forward pass,
   the direct on-ramp to 03-pretraining's training loop.

## Speedrun note

This track doesn't correspond to its own speedrun stage — it's the code that
`02-pretrain` (speedrun stage `02-pretrain`, track `03-pretraining`) is built
out of. Get comfortable here before starting the speedrun.
