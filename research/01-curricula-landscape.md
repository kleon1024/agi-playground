# The Open-Source LLM/ML Curriculum Landscape, Mid-2026

> Research pass conducted 2026-07-24 with parallel web-research agents; sources linked inline.

## 1. Karpathy's ecosystem (the reference lineage)

- **nn-zero-to-hero** — YouTube + repo series (micrograd → makemore → GPT). Pure from-scratch code pedagogy: build autograd, then a bigram model, then a Transformer, in raw PyTorch. Covers pretraining fundamentals and backprop intuition only. No data engineering, no RLHF/RL, no infra, no agents.
- **LLM101n** — an announced 17-chapter "build a Storyteller LLM" undergraduate curriculum spanning Python/C/CUDA. Largely stalled/incomplete as a standalone repo; its planned scope (tokenizer → pretrain → finetune → deploy) was effectively superseded and partially delivered by nanochat, which Karpathy calls its "capstone."
- **nanoGPT** — now explicitly deprecated by its own author in 2026 in favor of nanochat; covered pretraining only (single GPU/multi-GPU speedrun training), no chat/instruction-tuning, no RL, no serving.
- **nanochat** ("the best ChatGPT that $100 can buy") — the current flagship: a single, readable, ~8,000-line full-stack pipeline covering tokenizer training, pretraining, midtraining, SFT, and a chat web UI, runnable end-to-end on rented 8xH100s. It popularized a "speedrun" leaderboard (sub-3-hour GPT-2-grade runs by 2026) as a community benchmark. Notably light on RL post-training depth, near-absent on data curation/annotation methodology (uses off-the-shelf datasets), and no serving/inference-infra story beyond a toy web UI — no batching, quantization, or multi-node serving.
- **microgpt** (Feb 2026) — a further distillation: a single 200-line, dependency-free file implementing a custom autograd engine plus a tiny GPT, explicitly framed as "everything else is just efficiency." Purely a pedagogical minimalism artifact; zero coverage of scaling, data, RL, or infra by design.

## 2. Stanford CS336 — Language Modeling from Scratch

The most systems-rigorous academic offering. Five assignments: (1) tokenizer + Transformer + optimizer from scratch, (2) profiling and a hand-written Triton FlashAttention2 kernel plus distributed-training systems work, (3) scaling-law fitting, (4) turning raw Common Crawl into filtered/deduplicated pretraining data, (5) SFT + RL (math reasoning) with optional safety alignment. This is the closest thing to a complete pretraining-to-alignment stack in an academic course, and uniquely strong on **systems/kernels and data filtering**. What it doesn't cover: multimodality, prompt engineering/downstream NLP tasks, production inference serving, or agent/tool-use harnesses — RL coverage is a single capstone assignment, not a deep RL curriculum.

## 3. Sebastian Raschka — "Build a Large Language Model (From Scratch)" + "Build a Reasoning Model (From Scratch)"

The book/repo pair is the most polished **notebook-and-prose** pedagogy (vs. terse research code): incremental PyTorch chapters building GPT-2-style pretraining, then instruction-tuning. The 2025 follow-up, `reasoning-from-scratch`, extends this into building a reasoning LLM step by step (chain-of-thought SFT, verifier-style rewards, distillation from reasoning traces). Strength: clarity and completeness for a single learner on a laptop/single GPU. Gap: no distributed systems/infra, no large-scale data pipeline work, and RL treatment is comparatively light/simplified next to CS336 or dedicated RL frameworks (no GRPO-at-scale, no multi-turn agentic RL).

## 4. Hugging Face's course family

- **smol-course** — practical alignment/fine-tuning course built around SmolLM3/SmolVLM2; runs on modest hardware, notebook-driven, covers SFT/DPO-style alignment for small models. Does not cover pretraining-from-scratch or large-cluster infra.
- **Ultra-Scale Playbook / nanotron** — the definitive open reference for multi-GPU/multi-node pretraining systems (parallelism strategies, GPU cluster orchestration), documentation-and-interactive-plot style rather than a graded course. Pure infra; no data curation or post-training content.
- **Smol Training Playbook (2025-26)** — HF's capstone "how we built SmolLM3" narrative: ablations, architecture/data-mix decisions, and a genuinely strong post-training chapter (SFT, DPO, GRPO, model merging) plus an infrastructure chapter. Long-form blog/docs style, not exercises — you read it, you don't build along.
- **agents-course** and **reasoning-course** (Open R1) — the former is a certificate-bearing intro to agent fundamentals (tool use, frameworks); the latter walks through reproducing DeepSeek-R1-style RL (GRPO) reasoning training. Together they're the most direct "agents + RL reasoning" curricular content HF ships, but each is narrow and somewhat shallow next to a dedicated systems course.

## 5. fast.ai

Still free, top-down, notebook-first ("Practical Deep Learning for Coders"), now folding in foundation-model fine-tuning and deployment patterns. Strong on democratized practical skill-building and ethics; weak/absent on frontier-scale pretraining, RL post-training, and infra — it remains oriented at practitioners applying existing models, not building frontier LLMs from scratch.

## 6. MIT/Berkeley systems courses

MIT's **6.5940 (TinyML and Efficient Deep Learning Computing)**, covering quantization, pruning, NAS, and LLM/diffusion-specific acceleration, was on hiatus (instructor sabbatical) into 2025-26 — a notable gap in currently-running academic inference-efficiency content. Berkeley's **CS294/194-196 "LLM Agents"** is the most visible academic agents course (agent foundations, task-automation capabilities, agent-development infra), and a newer **CS294-288** (Sewon Min, Fall 2026) focuses on LLM data and development. These are agent- and data-centric respectively, but neither is a soup-to-nuts pretraining+RL+infra sequence like CS336.

## 7. Notable 2025-2026 research-adjacent "education by codebase"

**TinyZero** (minimal DeepSeek-R1-Zero reproduction on countdown/multiplication tasks, ~$30, built on **verl**) and **verl** itself (ByteDance's now-de-facto open GRPO/agentic-RL training backbone) function as de facto RL-post-training curricula by example, alongside newer research repos (Tree-GRPO, Open-AgentRL) that are more research artifacts than teaching material — dense, less annotated, assuming strong prior background.

## Gap Analysis: What a Differentiated 2026 Zero-to-Mastery Repo Needs

No single existing resource spans the full stack with equal depth. The clearest white space:

1. **Data pipelines and annotation as a first-class module** — every "from scratch" repo (nanochat, Raschka, microgpt) treats data as already-clean; even CS336's data assignment stops at filtering/dedup of Common Crawl. None teach human/LLM-assisted annotation, preference-data collection, rubric design for RLVR reward functions, or data QA/versioning at production quality — a glaring gap given how central data curation is to real frontier labs.
2. **RL post-training in the GRPO/RLVR era, taught progressively** — CS336 gives one assignment, Raschka's reasoning book is simplified, and verl/TinyZero are research code without teaching scaffolding. A differentiated curriculum needs a graduated path: reward-model basics → DPO → GRPO/RLVR → multi-turn agentic RL → async/distributed RL training, each with runnable, annotated code at increasing scale.
3. **Inference infrastructure as a taught subject, not just docs** — Ultra-Scale Playbook and 6.5940 cover training-time parallelism and compression respectively, but serving-time concerns (continuous batching, KV-cache management, speculative decoding, quantized serving, multi-tenant routing) have no equivalent hands-on, exercise-driven course; this is presently only "read the vLLM/SGLang source."
4. **Agent harness engineering** — HF's agents-course and Berkeley's CS294-196 introduce agent concepts, but neither teaches building a robust harness itself: sandboxing/tool execution, context management and compaction, multi-agent orchestration, evaluation/tracing of agentic loops, and failure-mode debugging. This is the single least-served topic given how central agent products have become by 2026.

A repo that chained data curation → pretraining (nanochat-grade) → GRPO-era post-training (verl-grade) → inference serving (vLLM/SGLang-grade) → agent harness construction, with runnable code at every stage and a coherent narrative connecting them, would fill a real and currently unoccupied niche.
