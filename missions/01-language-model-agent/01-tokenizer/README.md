---
status: draft
---

# Speedrun 01 — Tokenizer

## Goal

Train our own byte-pair encoding tokenizer on the speedrun corpus, rather than
reusing an off-the-shelf vocabulary.

## Deliverable

A minbpe-style BPE tokenizer, ~8-16k vocabulary, trained on the `00-corpus`
shard.

## Anchor project

minbpe (see `platform/training/LANDSCAPE.md` for the toy/production
mapping). Seed lesson: `platform/training/README.md`,
`01-bpe-tokenizer-from-scratch`.

## Verification criterion

No verified run yet — depends on `00-corpus` landing first. When trained, its
`runs/` entry must show: the exact training command and config (vocab size,
merge count), wall-clock time, the resulting vocabulary size, and round-trip
encode/decode correctness on a held-out sample of the corpus.
