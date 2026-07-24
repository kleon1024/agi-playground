---
status: draft
---

# 04 — Post-training

## Scope

Turning a pretrained base model into something useful and steerable: SFT and
chat-tuning, parameter-efficient fine-tuning (LoRA/PEFT), reward model
training, the DPO family of preference-optimization losses, distillation, and
model merging. This track stops short of RL-as-a-loop (PPO/GRPO/RLVR) — that's
`05-rl`, taught progressively rather than as one capstone assignment.

## Prerequisites

`03-pretraining` — this track needs a base checkpoint to fine-tune. Any small
open checkpoint works if you haven't run the pretraining track yourself.

## Planned lessons

1. `01-sft-chat-tuning` — chat templates, loss masking, instruction tuning on
   a small open dataset.
2. `02-lora-and-peft` — low-rank adapters, why they work, when full-parameter
   fine-tuning is still worth it.
3. `03-reward-model-training` — training a scalar reward model from preference
   data.
4. `04-dpo-family-loss-diffs` — DPO, IPO, KTO, ORPO, SimPO as "diff the loss
   function" exercises against a shared training loop.
5. `05-distillation` — teacher-student distillation, reasoning-data curation
   (OpenThoughts-style).
6. `06-model-merging` — weight averaging and merging techniques for combining
   fine-tuned checkpoints.

## Speedrun note

`01-sft-chat-tuning` is the seed lesson for speedrun stage `03-sft` (chat
template + loss masking on a small open instruct set, with before/after
samples).
