---
status: draft
level: reference
---

# RL: Landscape

Source: `research/synthesis.md` anchor table, "GRPO/RLVR" and "Agentic RL"
rows, plus the "Key 2025-2026 shifts" notes on RLVR/GRPO/GSPO/DAPO status.

| Toy (teach-from) | Production | Our take |
|---|---|---|
| TRL `GRPOTrainer`, TinyZero (unscaffolded but canonical R1-style repro) | verl (the DeepSeek-R1/Qwen reproduction standard), OpenRLHF, prime-rl | TRL's `GRPOTrainer` is the readable entry point; TinyZero is worth reading once as the "how small can a real repro get" reference, not as a starting template. verl is the field's de facto standard for serious repros — naming OpenRLHF and prime-rl alongside it keeps this lesson from depending on any one project's roadmap. PPO is taught in `01-ppo-grounding` as the algorithm GRPO simplifies away from (no separate value network); GSPO and DAPO (`03-gspo-dapo-diffs`) are documented as diffs against this same GRPO implementation rather than as separate anchors. |
| verifiers (an "environment = reward function" framing) | prime-rl + Environments Hub, SkyRL | Agentic/multi-turn RL is the field's current frontier, per the synthesis — this is intentionally the last lesson in the track. verifiers keeps the toy small enough to read; prime-rl/Environments Hub and SkyRL are the two production ecosystems worth knowing, one community-hub-centric and one more infra-focused. |

**Single-vendor-rot note:** both rows name multiple independent production
projects. GRPO+LoRA is comfortable at 0.5-3B on the single-GPU lane; larger rollout
concurrency for agentic RL moves to the Modal lane.
