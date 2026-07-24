---
status: draft
---

# Speedrun 04 — RL

## Goal

Apply RL post-training to the chat-tuned model on a task with a verifiable
reward signal.

## Deliverable

GRPO training on a verifiable task (e.g. arithmetic or Countdown-style
number puzzles) with LoRA, with a published reward curve over training.

## Anchor project

TRL `GRPOTrainer` / TinyZero (see `tracks/05-rl/LANDSCAPE.md` for the
toy/production mapping). Seed lesson: `tracks/05-rl/README.md`, `02-grpo`
(building on `01-ppo-grounding` and `04-rlvr` for the reward-design context).

## Verification criterion

No verified run yet — depends on `03-sft` landing first. When trained, its
`runs/` entry must show: the exact GRPO training command and config (task
definition, reward function, LoRA rank, group size), wall-clock time, and a
Trackio-exported reward curve over training steps.
