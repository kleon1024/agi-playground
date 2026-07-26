# agi-playground

Learn the full modern AI stack by building it: data → pretraining → post-training →
RL → inference → evals → agent harnesses. Readable from-scratch cores, production-tool
lanes, and real, verified runs — most of it on a single 24GB GPU.

## Why this exists

No existing resource spans the full stack with equal depth. From-scratch repos like
nanochat, Sebastian Raschka's books, and microgpt teach pretraining well and stop
there; RL courses cover one algorithm as a capstone assignment; inference is usually
"go read the vLLM source"; and agent harness engineering — loop design, tool schemas,
context management, sandboxing, sub-agents, harness-aware evals — is barely taught
anywhere. A 2026-07 research pass across curricula, pretraining+data, post-training/RL, and
infra/harness landscapes (see [`research/`](research/)) confirmed the gap and shaped
this repo's scope.

The white space this repo targets: data pipelines and annotation as a first-class
module (not "assume the corpus is already clean"); RL post-training taught
progressively — reward models → the DPO family → GRPO/RLVR → agentic multi-turn RL —
instead of one unscaffolded jump; inference infra as an exercise-driven subject
instead of a source-reading assignment; and agent harness engineering treated as its
own discipline, not an afterthought bolted onto a model demo.

The pedagogy, validated across all four research surveys, is **read the toy, then map
to the real thing**: every topic pairs a minimal, fully readable implementation with
the production system it mirrors, then tells you when to reach for which.

| Toy | Production |
|---|---|
| minbpe | HF tokenizers |
| nanoGPT | torchtitan / OLMo-core |
| TRL toy GRPO | verl |
| nano-vLLM | vLLM |
| mini-swe-agent | Claude Code / OpenHands |
| Trackio | wandb |

## The speedrun

The flagship path: raw text in, your own chat agent out, in eight stages, every stage
genuinely running on one 24GB GPU. Each stage is a from-scratch core wired to the
next — the speedrun is the integration test for the tracks below. If a track's core
lesson breaks, the speedrun breaks.

| Stage | Deliverable | Anchor | Status |
|---|---|---|---|
| [00 · corpus](speedrun/00-corpus/) | Cleaned English shard from Common Crawl/FineWeb via datatrove; dedup + quality-filter stats | datatrove | ✅ [built](speedrun/00-corpus/runs/) |
| [01 · tokenizer](speedrun/01-tokenizer/) | Own BPE tokenizer, minbpe-style, trained on the shard | minbpe | 🚧 planned |
| [02 · pretrain](speedrun/02-pretrain/) | ~120M-class decoder (RMSNorm/RoPE/SwiGLU), bf16, grad-accum; loss curve published | nanoGPT / nanochat | 🚧 planned |
| [03 · sft](speedrun/03-sft/) | Chat template + loss masking on a small open instruct set; before/after samples | TRL | 🚧 planned |
| [04 · rl](speedrun/04-rl/) | GRPO on a verifiable task with LoRA; reward curve | TRL GRPOTrainer / TinyZero | 🚧 planned |
| [05 · serve](speedrun/05-serve/) | Minimal engine: KV cache → paged blocks → continuous batching; benchmarked vs. naive generate | nano-vLLM | 🚧 planned |
| [06 · agent](speedrun/06-agent/) | Minimal harness: loop, 2-3 tools, context window management, sandboxed execution | mini-swe-agent | 🚧 planned |
| [07 · eval](speedrun/07-eval/) | Perplexity + small task suite + harness-disclosed agent eval; one honest report | lm-eval, inspect-ai | 🚧 planned |

Success looks like one documented command per stage, end-to-end wall-clock and cost,
and a final report a newcomer can reproduce.

## Curriculum map

Tracks are numbered for reading order but each is self-contained enough to enter
directly — every track states its own prerequisites. Every track has a written
guide; `🚧 draft` means its lessons are not yet built and run. A track is only
marked otherwise once it contains a lesson with a recorded run behind it.

| # | Track | Scope | Status |
|---|---|---|---|
| 01 | [Foundations](tracks/01-foundations/) | Tensors → autograd → attention → transformer | ✅ [1 lesson verified](tracks/01-foundations/01-first-training-loop/) |
| 02 | [Data](tracks/02-data/) | Pipelines, dedup/filtering, annotation, synthetic data | ✅ [seeded by speedrun 00](speedrun/00-corpus/) |
| 03 | [Pretraining](tracks/03-pretraining/) | Tokenizers, architectures, training loop, scaling laws | 🚧 draft |
| 04 | [Post-training](tracks/04-post-training/) | SFT, LoRA/PEFT, reward models, DPO family, distillation, merging | 🚧 draft |
| 05 | [RL](tracks/05-rl/) | PPO grounding → GRPO/GSPO/DAPO → RLVR → agentic RL + environments | 🚧 draft |
| 06 | [Inference](tracks/06-inference/) | KV cache → paged attention → batching → spec decode → quantization; training infra (FSDP2, profiling) | 🚧 draft |
| 07 | [Evals](tracks/07-evals/) | lm-eval-harness, inspect-ai, agent/harness-aware evals | 🚧 draft |
| 08 | [Agents](tracks/08-agents/) | Harness engineering: loop, tools, context management, sandboxing, multi-agent | 🚧 draft |

## How lessons work

Every lesson is a directory with the same anatomy:

```
tracks/05-rl/03-grpo/
├── README.md    # intuition → math → implementation walk-through → production notes → exercises
├── core/        # from-scratch: pure PyTorch + stdlib, minimal deps, heavily commented
├── prod/        # the same thing with real tools (TRL/verl/vLLM/...), config included
└── runs/        # verified run logs: exact command, config, hardware, wall-clock, cost, metrics
```

`core/` teaches mechanics, `prod/` teaches practice — both must actually run. The
honesty rule: a lesson without a verified run in `runs/` is marked `status: draft`
in its README frontmatter and shows as draft in the tables above. Nothing here
claims a result it has not reproduced, and every number published in a lesson is
traceable to a `runs/` entry naming the command, hardware, and wall-clock that
produced it.

## Hardware

Two compute lanes, documented as content in [`infra/`](infra/), not just a setup
footnote:

- **Local — RTX 4090, 24GB.** Reached via Tailscale SSH into WSL2 (setup
  documented and verified end-to-end — see
  [`infra/local-4090.md`](infra/local-4090.md)). Fits every
  `core/` toy, GPT-2-class pretraining, ≤8B LoRA SFT, GRPO on 0.5-3B models,
  datatrove data shards, and all inference/harness/eval labs.
- **Cloud — Modal.** Used for 2-4 GPU parallelism labs (FSDP2/TP/PP), 7B+
  full-parameter work, GPU-scale dedup, and RL rollout concurrency. Every Modal
  lesson prints its dollar cost in `runs/`.

Tracking is Trackio (local-first, source readable in one sitting) with wandb as an
optional alternative.

## Status & roadmap

Current milestone: **M1 — Speedrun v0**.

- **M0 — Scaffold (done):** repo structure, README manifesto + curriculum map,
  license, CI, `research/` published, written guides for all eight tracks, and
  both `infra/` lanes verified with recorded output — Modal hello-GPU and the
  4090/WSL2 CUDA smoke test.
- **M1 — Speedrun v0 (in progress):** the eight stages above, in order, each
  landing its seed lesson(s) in the corresponding track. Stage 00 (corpus) is
  built and recorded; stage 01 (tokenizer) is next.
- **M2 — Post-training + RL deepened:** DPO-family loss diffs, RM training,
  rejection sampling, distillation, merging; Tulu-3/R1 recipe walkthroughs.
- **M3 — Data track deepened:** FineWeb-style pipeline lab, quality classifiers,
  Argilla+distilabel annotation loop, preference-data + RLVR rubric design.
- **M4 — Inference + infra deepened:** speculative decoding, quantization,
  disaggregation concepts; FSDP2 + profiling labs; Modal multi-GPU parallelism lab.
- **M5 — Agents + evals deepened:** harness patterns (context compaction,
  sub-agents, sandboxing), τ²-bench-style environment design, harness-disclosed
  evaluation methodology.

Milestones ship sequentially; within a milestone, lessons land as they're verified.

## Research

[`research/`](research/) holds the published landscape research and positioning
behind this curriculum — the four-survey pass (curricula, pretraining+data,
post-training+RL, infra+harness) that identified the gap this repo fills. It's kept
as a standing credibility artifact and updated periodically as the field moves.

## License

MIT.
