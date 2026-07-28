---
label: Post-training and RL
---

# LLM Post-Training & RL: 2026 Landscape for a Teaching Repo

> Research pass conducted 2026-07-24 with parallel web-research agents; sources linked inline.

## (a) Frameworks — maturity and best-fit

| Framework | Maturity | Best at | Learnability |
|---|---|---|---|
| **HF TRL** | Most mature, widest adoption | SFT/DPO/PPO/GRPO for single-node to ~30B with Accelerate/FSDP; best docs, richest ecosystem | Highest — clean `SFTTrainer`/`DPOTrainer`/`GRPOTrainer` APIs, good for teaching the algorithm shape without infra noise |
| **OpenRLHF** | Production-grade, Ray+vLLM native | Async agentic RL at scale (PPO, DAPO, REINFORCE++, TIS), generation/training colocation; reportedly faster than verl on long-context 14B runs | Medium — more moving parts (Ray actors) but codebase is still readable |
| **verl (ByteDance/Seed)** | Very mature, widely used for reasoning-model repros | HybridFlow architecture; the de-facto framework people use to reproduce DeepSeek-R1/Qwen-style GRPO/DAPO/GSPO recipes; strong multi-node scaling | Medium-low — powerful but architecturally dense (Ray + multiple backends) |
| **AllenAI open-instruct** | Mature, research-first | The literal codebase behind Tulu 3/Tulu 3.1+; full SFT→DPO→RLVR pipeline is fully documented and reproducible end-to-end | High for *reading a real recipe*, but less "framework," more "repo that produced Tulu" |
| **axolotl** | Production-ready (v0.8.x+) | Deepest parallelism matrix (FSDP2, DeepSpeed, TP, CP, EP), config-driven YAML, now including GRPO + reward-model support | Medium — YAML-first, less code to read than TRL internals |
| **LLaMA-Factory** | Mature, broadest model coverage | Web UI, fastest path to "first fine-tune," Unsloth-backend option | Highest for beginners, lowest for internals-curious learners |
| **unsloth** | Mature, single-GPU specialist | 2–5x speed, ~70% less VRAM via custom kernels; now supports FP8 GRPO fitting Qwen3-1.7B into ~5GB | High — small, hackable core; the best on-ramp for a 4090 curriculum |
| **torchtune** | Mature but narrower scope | Clean PyTorch-native recipes, torch.compile gains (~20-24%) | Highest for reading undecorated PyTorch training loops |
| **PrimeIntellect prime-rl + verifiers** | Newer (2025-2026), fast-moving | Fully async agentic RL at 1000+ GPU scale, first-class integration with the **Environments Hub** (`prime env install`) for tool-use/SWE/math environments | Medium — the `verifiers` library itself is small and a great teaching artifact for "environment = reward function" |
| **NVIDIA NeMo-RL** | Mature, used for Nemotron post-training | Ray-based multi-node/multi-GPU RL, ancestor/inspiration for verl, SkyRL, ROLL | Low-medium — enterprise-oriented, heavier stack |

**Recommendation for a teaching repo:** use **TRL + unsloth** for the pedagogical core (SFT/DPO/GRPO on 0.5–3B models), point to **open-instruct** and **verl** as "read the real recipe" reference repos, and use **verifiers/prime-rl** or **SkyRL-Gym** as the module on agentic/multi-turn RL.

## (b) Algorithms a 2026 curriculum must teach

- **SFT** — foundation; teach with torchtune or TRL's `SFTTrainer` for a clean loop.
- **LoRA/QLoRA** — PEFT via unsloth; single clearest reference is the original QLoRA repo plus unsloth's kernels.
- **Reward models** — Bradley-Terry classifier heads; TRL's `RewardTrainer` is the cleanest minimal implementation. Note the 2026 shift toward "reward-as-reasoning" (RM-R1) as an advanced topic.
- **PPO** — still taught for historical/conceptual grounding (critic + clipped objective), but de-emphasized in practice.
- **DPO and variants** — DPO, then **IPO, KTO** (unpaired/binary feedback), **ORPO** (reference-free, merges SFT+alignment), **SimPO** (reference-free, length-normalized reward). All have compact TRL trainer implementations — good for a "diff the loss function" exercise.
- **GRPO** — the 2026 default: no critic, group-normalized advantages `(r_i - mean)/std`. DeepSeek-R1's core algorithm; minimal reference: TRL's `GRPOTrainer` or Will Brown's/Hugging Face's toy GRPO scripts.
- **GSPO** (Qwen team) — sequence-level rather than token-level importance ratios; fixes GRPO instability at MoE scale.
- **DAPO** (ByteDance/Tsinghua) — clip-higher, dynamic sampling, overlong-reward shaping; open-sourced reference code exists and is a good "diff vs GRPO" exercise.
- **RLVR** — the umbrella paradigm (rule/programmatic reward instead of a learned RM) powering DeepSeek-R1, Qwen3, and Tulu 3's RL stage. Teach this as the conceptual anchor, with GRPO/DAPO/GSPO as concrete instances.
- **Rejection sampling (+ SFT)** — DeepSeek-R1's stage 3: sample many, filter by verifier/RM, SFT on the winners. Simple to reimplement and a good bridge between SFT and RL.
- **Distillation** — reasoning-trace distillation (OpenThoughts/OpenThinker style) and newer **on-policy distillation** (Thinking Machines' formulation) as the 2026 refinement.
- **Model merging** — mergekit (task-arithmetic, SLERP, TIES/DARE) as a cheap, GPU-light lab exercise.

## (c) Recipes worth studying end-to-end

- **Tulu 3 / open-instruct** (AllenAI) — the most fully-documented open recipe: SFT → DPO → RLVR, with public data, code, and eval harness. No LoRA/quantization used in the original recipe (full fine-tune), which is itself a useful teaching contrast against the unsloth/LoRA path.
- **DeepSeek-R1** — cold-start SFT → large-scale RLVR → rejection-sampling+SFT → all-scenario RL (RLVR + preference reward). The canonical four-stage pipeline to diagram.
- **Qwen3** — mirrors the R1 recipe at larger scale; GSPO originates from this line of work.
- **SmolLM3 / SmolLM post-training** (Hugging Face) — smaller, more reproducible reference for students, good complement to Tulu 3.
- **OpenThoughts / OpenThinker (1→3)** — reasoning-data curation recipes; OpenThoughts3-7B hits strong AIME/LiveCodeBench numbers from public data only, ideal as a distillation-dataset case study.

## (d) Hardware feasibility on a single RTX 4090 (24GB) vs. Modal multi-GPU

- **Fits on one 4090:** SFT/LoRA/QLoRA up to ~7-8B; DPO/ORPO/SimPO on 1-3B full or 7-8B LoRA; reward-model training on ≤3B. **GRPO with LoRA on 0.5-3B models is comfortably feasible** — unsloth's FP8 GRPO path fits Qwen3-1.7B in ~5GB, leaving headroom for larger batch/group sizes or a 3B model.
- **Needs Modal / multi-GPU:** full-parameter RL on 7B+ (rollout + training + reference model memory triples up), multi-node async RL (OpenRLHF/verl/NeMo-RL/prime-rl territory), any DAPO/GSPO reproduction at the scale reported in papers, and agentic multi-turn RL with real tool/browser environments where rollout concurrency dominates cost.

## Notable 2025-2026 shifts to flag in the curriculum

Agentic RL and **multi-turn environments** are now the frontier: PrimeIntellect's **verifiers + Environments Hub** (`prime env install`) standardizes "environment as installable package," and **prime-rl** trains against them asynchronously at 1000+ GPU scale. **SkyRL** (NovaSky/Berkeley) pioneered open long-horizon agent RL (SWE-Bench-style, now integrated with Harbor for terminal agents) and implements the Tinker API for running on local GPUs. NeMo-RL is explicitly the architectural ancestor of both verl and SkyRL. A capstone module pairing `verifiers` (write a custom reward/environment) with a small GRPO run is the highest-leverage 2026 addition to any post-training curriculum.

## Sources

[Spheron: verl/OpenRLHF/TRL](https://www.spheron.network/blog/rlhf-training-infrastructure-verl-openrlhf-trl-gpu-cloud/), [OpenRLHF GitHub](https://github.com/openrlhf/openrlhf), [llm-stats: Post-Training 2026](https://llm-stats.com/blog/research/post-training-techniques-2026), [PrimeIntellect prime-rl](https://github.com/PrimeIntellect-ai/prime-rl), [PrimeIntellect verifiers](https://github.com/PrimeIntellect-ai/verifiers), [Environments Hub docs](https://docs.primeintellect.ai/tutorials-environments/environments), [SkyRL GitHub](https://github.com/NovaSky-AI/SkyRL), [SkyRL-v0 post](https://novasky-ai.github.io/posts/skyrl-v0/), [Tulu 3 technical](https://allenai.org/blog/tulu-3-technical), [open-instruct GitHub](https://github.com/allenai/open-instruct), [Tulu 3 arXiv](https://arxiv.org/abs/2411.15124), [MarkTechPost fine-tuning comparison 2026](https://www.marktechpost.com/2026/07/22/unsloth-vs-axolotl-vs-trl-vs-llama-factory-a-fine-tuning-framework-comparison-on-speed-vram-and-multi-gpu/), [Spheron: Axolotl vs Unsloth vs TorchTune](https://www.spheron.network/blog/axolotl-vs-unsloth-vs-torchtune/), [Unsloth FP8 RL docs](https://unsloth.ai/docs/get-started/reinforcement-learning-rl-guide/fp8-reinforcement-learning), [OpenThoughts arXiv](https://arxiv.org/abs/2506.04178), [Thinking Machines: on-policy distillation](https://thinkingmachines.ai/blog/on-policy-distillation/), [DPO variants guide](https://mbrenndoerfer.com/writing/dpo-variants-ipo-kto-orpo-cdpo-llm-alignment), [NVIDIA-NeMo/RL GitHub](https://github.com/nvidia-nemo/rl), [NeMo-RL docs overview](https://docs.nvidia.com/nemo/rl/latest/about/overview.html), [verl-project GitHub](https://github.com/verl-project/verl).
