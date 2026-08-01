---
level: reference
---

# agi-playground — Research Synthesis (2026-07-24)

Four parallel research passes: curricula landscape, pretraining+data, post-training+RL, infra+agent harness.
Full reports live in the session task outputs; this file is the distilled synthesis for design.

## Positioning (the gap we fill)

No existing resource spans the full stack with equal depth. White space in 2026:
1. **Data pipelines + annotation as first-class module** — every from-scratch repo (nanochat, Raschka,
   microgpt) treats data as already clean. Nobody teaches annotation, preference-data collection,
   RLVR rubric design, data QA/versioning.
2. **RL post-training taught progressively** — RM basics → DPO → GRPO/RLVR → multi-turn agentic RL →
   async distributed RL. CS336 has one assignment; verl/TinyZero are research code without scaffolding.
3. **Inference infra as a taught, exercise-driven subject** — currently only "read vLLM source".
4. **Agent harness engineering** — the least-served topic: loop design, tool schemas, context
   management, sandboxing, sub-agents, harness-aware evals.

**Core pedagogy pattern (validated across all 4 reports): "read the toy, then map to the real thing"**
— pair a minimal fully-readable implementation with the production system it mirrors:
nano-vLLM ↔ vLLM · mini-swe-agent ↔ OpenHands/Claude Code · minbpe ↔ HF tokenizers ·
nanoGPT/nanochat ↔ torchtitan/OLMo-core · TRL toy GRPO ↔ verl · Trackio ↔ wandb.
This matches our locked decision: from-scratch core + production lane, both verified by real runs.

## Canonical anchors per track

| Track | Teach-from (toy) | Production reference | Single-GPU (24GB)? |
|---|---|---|---|
| Tokenizer | minbpe | HF tokenizers, tiktoken, SentencePiece | yes |
| Pretraining | nanoGPT → nanochat spine, modded-nanoGPT speedrun | torchtitan, nanotron, OLMo-core, Megatron (read-only) | GPT-2 124M–350M class |
| Data pipeline | datatrove on CC shards (reruns published FineWeb stages) | NeMo Curator (GPU, Modal), dolma, DCLM methodology | yes (CPU-bound) |
| Annotation/synthetic | distilabel + Argilla; Label Studio for generic | same | yes |
| SFT/PEFT | TRL SFTTrainer, torchtune clean loops | axolotl, LLaMA-Factory, unsloth kernels | ≤7-8B LoRA |
| RM/DPO family | TRL trainers ("diff the loss function" exercises: DPO/IPO/KTO/ORPO/SimPO) | open-instruct (Tulu 3 recipe) | 1-3B full, 7-8B LoRA |
| GRPO/RLVR | TRL GRPOTrainer, TinyZero | verl (DeepSeek-R1/Qwen repro standard), OpenRLHF, prime-rl | GRPO+LoRA 0.5-3B comfortable; unsloth FP8 GRPO fits 1.7B in ~5GB |
| Agentic RL | verifiers (environment = reward function) | prime-rl + Environments Hub, SkyRL | small envs yes; real rollout concurrency → Modal |
| Inference | nano-vLLM (~1.2k lines: paged KV, scheduling, prefix cache) | vLLM ("Anatomy of vLLM"), SGLang, Dynamo disagg | yes for concepts |
| Training infra | 1-GPU: grad accum, act ckpt, mixed precision; profiling labs (PyTorch Profiler → Nsight) | FSDP2 (DTensor), DeepSpeed for MoE/offload; TP/PP on Modal 2-4 GPU | split local/Modal |
| Evals | lm-eval-harness; inspect-ai | inspect_evals (AgentThreatBench), SWE-bench Pro, Terminal-Bench 2.0, τ²-bench, GAIA | yes |
| Agent harness | mini-swe-agent (read in one sitting); build-your-own harness | SWE-agent (ACI), OpenHands, Claude Code write-ups, smolagents | yes (API models) |
| Tracking | Trackio (<1k lines, readable) | wandb | yes |

## Recipes worth teaching end-to-end
- Tulu 3 / open-instruct: SFT → DPO → RLVR, fully documented.
- DeepSeek-R1 four-stage: cold-start SFT → RLVR → rejection sampling+SFT → all-scenario RL.
- SmolLM3 + Smol Training Playbook: ablation-driven decisions narrative.
- OpenThoughts: reasoning-data curation / distillation case study.

## Key 2025–2026 shifts to encode
- nanochat (Oct 2025) is the bar for full-stack teaching repos; nanoGPT deprecated by its author.
- RLVR is the umbrella paradigm; GRPO the default algorithm; GSPO/DAPO as diffs; PPO taught for grounding.
- Agentic/multi-turn RL + environments (verifiers, Environments Hub, SkyRL) = frontier capstone.
- Prefill/decode disaggregation is the dominant production serving pattern; speculative decoding (EAGLE-3) is default-on.
- FSDP2 default for 2-8 GPU; Muon-optimizer speedruns show systems tricks rival architecture.
- Harness disclosure matters: "Stop Comparing LLM Agents Without Disclosing the Harness" — harness design IS the independent variable (great framing for the agents track).
- Cautionary tale: Lilac acquired+archived — don't anchor curriculum on single-vendor tools.

## Compute lanes
- Local: RTX 4090 24GB via SSH → WSL2 (Tailscale). Fits: all toys, GPT-2-class pretrain, ≤8B LoRA,
  GRPO on 0.5-3B, datatrove shards, all inference/harness/eval labs.
- Cloud: Modal (keys exist in other projects). Fits: multi-GPU parallelism labs (2-4 GPU TP/PP),
  7B+ full-param RL, NeMo Curator GPU dedup, large rollout concurrency. Volumes for checkpoints.
- Tracking: Trackio local-first (readable source aligns with pedagogy), wandb optional.
