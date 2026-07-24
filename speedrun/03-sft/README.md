---
status: draft
---

# Speedrun 03 — SFT

## Goal

Turn the pretrained base model into a chat-tuned model via supervised
fine-tuning on a small open instruction dataset.

## Deliverable

Chat template applied with correct loss masking, fine-tuned on a small open
instruct set, with before/after sample completions published for comparison.

## Anchor project

TRL (see `tracks/04-post-training/LANDSCAPE.md` for the toy/production
mapping). Seed lesson: `tracks/04-post-training/README.md`,
`01-sft-chat-tuning`.

## Verification criterion

No verified run yet — depends on `02-pretrain` landing first. When trained,
its `runs/` entry must show: the exact SFT command and config (dataset,
chat template, learning rate, epochs), wall-clock time, and a set of
before/after sample completions on identical prompts (not cherry-picked
successes only).
