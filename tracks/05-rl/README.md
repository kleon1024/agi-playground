---
status: draft
---

# 05 — RL

## Scope

RL post-training taught progressively, not as one capstone assignment (CS336's
approach) or unscaffolded research code (verl, TinyZero used raw). The
progression: PPO for grounding the mechanics, GRPO as the modern default,
GSPO/DAPO as documented diffs against GRPO, RLVR as the umbrella paradigm for
verifiable-reward tasks, rejection sampling as a lighter-weight alternative,
and agentic/multi-turn RL with environments as the frontier capstone.

## Prerequisites

`04-post-training` (reward models and the DPO family establish the
preference-optimization context RL extends) and `03-pretraining` (a base or
SFT'd checkpoint to apply RL to).

## Planned lessons

1. `01-ppo-grounding` — PPO mechanics from scratch: advantage estimation,
   clipped objective, why it's the historical baseline.
2. `02-grpo` — group-relative policy optimization, the current default
   algorithm for LLM RL.
3. `03-gspo-dapo-diffs` — GSPO and DAPO as documented diffs against the GRPO
   baseline.
4. `04-rlvr` — reinforcement learning from verifiable rewards as the umbrella
   paradigm; rubric and reward-function design.
5. `05-rejection-sampling` — rejection sampling + SFT as a lighter alternative
   to full RL loops (the DeepSeek-R1 recipe's stage 3).
6. `06-agentic-rl-environments` — multi-turn agentic RL, environment design as
   reward-function design (the frontier capstone).

## Speedrun note

`02-grpo` is the seed lesson for speedrun stage `04-rl` (GRPO on a verifiable
task — e.g. arithmetic/countdown — with LoRA, reward curve published).
