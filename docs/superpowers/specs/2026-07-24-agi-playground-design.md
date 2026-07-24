# agi-playground — Design Doc

**Date:** 2026-07-24 · **Owner:** kleon1024 · **Status:** Draft for review

## 1. What this is

An open-source, English-first monorepo that takes a software engineer from zero to
practitioner-level mastery of the modern AI stack: data pipelines and annotation,
LLM pretraining, post-training, RL, inference/infra, evals, and agent harness
engineering. Everything is implemented in-house at "readable toy" scale, mirrored
against production tools, and **verified by real runs** on real hardware.

GitHub: `github.com/kleon1024/agi-playground` · License: MIT.

## 2. Positioning (from the 2026-07 research pass)

Four parallel research surveys (curricula, pretraining+data, post-training+RL,
infra+harness; synthesis in `research/`) found no resource that spans the full
stack with equal depth. The white space:

1. **Data pipelines + annotation as a first-class module.** Every from-scratch
   repo (nanochat, Raschka, microgpt) treats data as already clean. Nobody teaches
   annotation, preference-data collection, RLVR rubric design, or data QA.
2. **RL post-training taught progressively** — RM → DPO family → GRPO/RLVR →
   agentic multi-turn RL — instead of one capstone assignment (CS336) or
   unscaffolded research code (verl, TinyZero).
3. **Inference infra as an exercise-driven subject**, not "go read vLLM source."
4. **Agent harness engineering** — the least-served topic in 2026: loop design,
   tool schemas, context management, sandboxing, sub-agents, harness-aware evals.

**Core pedagogy (validated across all surveys): "read the toy, then map to the
real thing."** Each topic pairs a minimal, fully readable implementation with the
production system it mirrors: minbpe↔HF tokenizers, nanoGPT↔torchtitan/OLMo-core,
TRL toy GRPO↔verl, nano-vLLM↔vLLM, mini-swe-agent↔Claude Code/OpenHands,
Trackio↔wandb.

## 3. Audience and promise

Software engineers with Python and basic math (no ML background required beyond
Track 01). The promise: finish the curriculum and you can clean a corpus, train a
tokenizer and a small LLM, post-train it with SFT + GRPO, serve it with an
inference engine you understand line-by-line, wrap it in an agent harness you
built, and evaluate all of it honestly — then operate the production equivalents.

## 4. Repo architecture

```
agi-playground/
├── README.md              # manifesto + curriculum map + speedrun quickstart
├── speedrun/              # FLAGSHIP: raw text → your own chat agent, on one 4090
│   ├── 00-corpus/         #   datatrove-cleaned shard
│   ├── 01-tokenizer/      #   own BPE
│   ├── 02-pretrain/       #   ~120M-class GPT, nanoGPT-style
│   ├── 03-sft/            #   chat-tune
│   ├── 04-rl/             #   tiny GRPO on a verifiable task
│   ├── 05-serve/          #   minimal paged-KV inference engine
│   ├── 06-agent/          #   minimal harness wrapping the served model
│   └── 07-eval/           #   eval report for every stage
├── tracks/
│   ├── 01-foundations/    # tensors → autograd → attention → transformer
│   ├── 02-data/           # pipelines, dedup/filtering, annotation, synthetic data
│   ├── 03-pretraining/    # tokenizers, architectures, training loop, scaling laws
│   ├── 04-post-training/  # SFT, LoRA/PEFT, reward models, DPO family, distillation, merging
│   ├── 05-rl/             # PPO grounding → GRPO/GSPO/DAPO → RLVR → agentic RL + environments
│   ├── 06-inference/      # KV cache → paged attention → batching → spec decode → quantization; training infra: FSDP2, profiling
│   ├── 07-evals/          # lm-eval-harness, inspect-ai, agent/harness-aware evals
│   └── 08-agents/         # harness engineering: loop, tools, context mgmt, sandboxing, multi-agent
├── infra/                 # lane setup: 4090/WSL2 via Tailscale SSH, Modal patterns, Trackio
├── research/              # published landscape research + positioning (credibility artifact)
└── docs/                  # meta-docs, specs, contribution guide
```

- The **speedrun is the integration test**: every stage composes the from-scratch
  cores taught in the tracks. If a track's core lesson breaks, the speedrun breaks.
- Track numbering is reading order, but tracks are self-contained enough to enter
  directly (each states its prerequisites).

## 5. Lesson anatomy (the unit of content)

Every lesson is a directory:

```
tracks/05-rl/03-grpo/
├── README.md    # the chapter: intuition → math → implementation walk-through →
│                # production notes → exercises. English. Figures where they earn keep.
├── core/        # from-scratch implementation: pure PyTorch + stdlib, minimal deps,
│                # single-file where possible, heavily commented, runs on the 4090
├── prod/        # the same thing with real tools (TRL/verl/vLLM/...), config included
└── runs/        # VERIFIED run logs: exact command, config, hardware, wall-clock,
                 # cost, metrics/loss curves (Trackio export). No unverified claims.
```

Rules:
- `core/` teaches mechanics; `prod/` teaches practice. Both must actually run.
- `runs/` is the honesty mechanism: a lesson without a verified run is marked
  `status: draft` in its README frontmatter and excluded from the curriculum map.
- External projects are linked, never vendored; each track has a `LANDSCAPE.md`
  mapping toy ↔ production tools with our take on when to use what.

## 6. Speedrun v0 (Milestone 1 spec)

Tiny but real, every stage genuinely runs on the 4090:

| Stage | Deliverable | Anchor |
|---|---|---|
| 00 corpus | ~1-2GB cleaned English shard from Common Crawl/FineWeb via datatrove; dedup + quality filter stats | datatrove |
| 01 tokenizer | own BPE (minbpe-style), ~8-16k vocab, trained on the shard | minbpe |
| 02 pretrain | ~120M-class decoder (RMSNorm/RoPE/SwiGLU), bf16, grad-accum; hours-scale run; loss curve published | nanoGPT/nanochat |
| 03 sft | chat template + loss masking; small open instruct set; before/after samples | TRL |
| 04 rl | GRPO on a verifiable task (e.g. arithmetic/countdown) with LoRA; reward curve | TRL GRPOTrainer / TinyZero |
| 05 serve | minimal engine: KV cache → paged blocks → continuous batching; benchmarked vs naive generate | nano-vLLM |
| 06 agent | minimal harness (~mini-swe-agent scale): loop, 2-3 tools, context window mgmt, sandboxed exec | mini-swe-agent |
| 07 eval | perplexity + small task suite + harness-disclosed agent eval; one honest report | lm-eval, inspect-ai |

Success criterion: one command per stage, documented end-to-end wall-clock and
cost, and a final report a newcomer can reproduce.

## 7. Compute lanes

- **Local lane:** RTX 4090 24GB, reached via Tailscale SSH into WSL2. Fits: all
  `core/` toys, GPT-2-class pretraining, ≤8B LoRA SFT, GRPO on 0.5-3B, datatrove
  shards, all inference/harness/eval labs. `infra/` documents the full setup as a
  lesson (remote dev over Tailscale is itself teachable content).
- **Cloud lane:** Modal (existing account/keys). Fits: 2-4 GPU parallelism labs
  (FSDP2/TP/PP), 7B+ full-param work, GPU dedup at scale, RL rollout concurrency.
  Volumes for checkpoints. Every Modal lesson prints its dollar cost in `runs/`.
- **Tracking:** Trackio (local-first, source readable in one sitting — matches the
  pedagogy); wandb optional.

## 8. Tooling, CI, quality bar

- Python 3.12, `uv` for envs, `ruff` + `pytest`. One `pyproject.toml` per
  lesson-group where deps diverge (lessons stay independently runnable).
- GitHub Actions CI: lint + CPU unit tests on tiny fixtures (attention shapes,
  tokenizer round-trips, GRPO advantage math). GPU runs are NOT in CI — they are
  verified manually and recorded in `runs/` (CI checks `runs/` metadata schema).
- File size ≤800 lines; `core/` files aim for far less.
- Conventional commits; build/lint must pass before commit.

## 9. Mining the existing corpus

`~/maestro/projects/training/` (~124 Chinese tutorials, ~56k lines + 8 mini-projects)
is the private quarry: per lesson, we rewrite (not translate literally) the
relevant material into the new anatomy, updating for the 2026 state of the art
(the corpus predates GSPO/DAPO-era RLVR, nanochat, FSDP2-default, harness-aware
evals). The old repo stays private; no wholesale import.

## 10. Roadmap

- **M0 — Scaffold (now):** repo structure, README manifesto + curriculum map,
  license, CI, `infra/` lane setup verified (SSH into WSL2 + smoke CUDA run;
  Modal hello-GPU), `research/` published. Push to GitHub.
- **M1 — Speedrun v0:** the 8 stages above, in order. Each stage lands with its
  seed lesson(s) in the corresponding track.
- **M2 — Post-training + RL track deepened:** DPO-family loss diffs, RM training,
  rejection sampling, distillation, merging; Tulu-3/R1 recipe walkthroughs.
- **M3 — Data track deepened:** FineWeb-style pipeline lab, quality classifiers,
  Argilla+distilabel annotation loop, preference-data + RLVR rubric design.
- **M4 — Inference + infra deepened:** spec decode, quantization, disaggregation
  concepts; FSDP2 + profiling labs; Modal multi-GPU parallelism lab.
- **M5 — Agents + evals deepened:** harness patterns (context compaction,
  sub-agents, sandboxing), τ²-bench-style environment design, harness-disclosed
  evaluation methodology.
- **Ongoing:** speedrun leaderboard (community wall-clock/quality entries),
  periodic landscape updates in `research/`.

Milestones ship sequentially; within a milestone, lessons land as verified.

## 11. Risks

- **Scope.** The counter is the lesson anatomy: nothing ships without a verified
  run, and the speedrun forces integration honesty. Milestones are sequential.
- **4090 ceiling.** Managed by design: toys locally, scale on Modal with printed
  costs; we never claim frontier-scale results.
- **Single-vendor rot** (the Lilac lesson): production lanes always name ≥2
  alternatives in `LANDSCAPE.md`; toys depend only on PyTorch + stdlib.
- **Windows/WSL2 friction:** `infra/` treats it as content, not a footnote; CI
  stays platform-neutral (CPU, Linux runners).

## 12. Success criteria

- A newcomer can go from `git clone` to a served, agent-wrapped, self-trained
  model following only repo docs.
- Every published lesson has a `runs/` entry with reproducible command + metrics.
- The repo is citable as the reference "full-stack from scratch, verified"
  curriculum — the niche the research identified as unoccupied.
