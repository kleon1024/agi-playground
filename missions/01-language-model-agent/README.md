---
status: draft
---

# Speedrun — raw text to your own chat agent, on one GPU

## What this is

The flagship integration path of agi-playground: starting from raw crawl text
and ending with a served, agent-wrapped, self-trained model, entirely on a
single 24GB GPU. Every stage genuinely runs on that hardware — nothing here is
a claim about frontier-scale results, and nothing ships without a verified
run recorded in that stage's `runs/` directory (see the design doc, §5, for
the lesson/run anatomy).

This mission is the integration test for the platform: every stage composes the
from-scratch cores taught in [`platform/`](../../platform/) and
[`capabilities/`](../../capabilities/). If a platform lesson's core breaks, this
mission breaks. Each stage below names the layer it draws on and the production
anchor its `prod/` lane mirrors.

Its contract is [`mission.yaml`](mission.yaml), and it is worth reading before
the stages — particularly `does_not_prove`. This mission establishes that the
layers compose on one GPU. It does not beat a hosted frontier model on output
quality and does not claim to.

## Stage table

| Stage | Deliverable | Anchor | Layer | Status |
|---|---|---|---|---|
| [`00-corpus`](00-corpus/) | cleaned English shard from Common Crawl via a from-scratch pipeline, compared against datatrove's FineWeb recipe | datatrove | `platform/data` | ✅ built |
| [`01-tokenizer`](01-tokenizer/) | own byte-level BPE, 16,384 vocab, 4.50 chars/token; naive vs indexed 71x; export verified id-identical | minbpe | `platform/training` | ✅ built |
| [`02-pretrain`](02-pretrain/) | 88M decoder (RMSNorm/RoPE/SwiGLU/GQA), bf16, grad-accum; loss curve published | nanoGPT/nanochat | `platform/training` | 🔨 loop verified, awaiting GPU |
| `03-sft` | chat template + loss masking; small open instruct set; before/after samples | TRL | `platform/adaptation` | 🚧 planned |
| `04-rl` | GRPO on a verifiable task with LoRA; reward curve | TRL GRPOTrainer / TinyZero | `platform/adaptation` | 🚧 planned |
| `05-serve` | minimal engine: KV cache → paged blocks → continuous batching; benchmarked vs naive generate | nano-vLLM | `platform/serving` | 🚧 planned |
| `06-agent` | minimal harness: loop, 2-3 tools, context window management, sandboxed execution | mini-swe-agent | `capabilities/act-coordinate` | 🚧 planned |
| `07-eval` | perplexity + small task suite + harness-disclosed agent eval; one honest report | lm-eval, inspect-ai | `platform/evaluation-observability` | 🚧 planned |

## Success criterion

One command per stage. Wall-clock time and dollar cost documented end-to-end.
A final report a newcomer can reproduce by following only these docs — no
verified-run claim without the run to back it.

## How to use this

Run the stages in order — each depends on the previous stage's output
(shard → tokenizer → base model → chat model → RL'd model → served model →
agent → eval report). Each stage's `README.md` states its own goal,
deliverable, anchor project, and what its `runs/` entry must show once it's
executed and verified. None of these stages are executed yet; every stage
below is `status: draft` until it has a verified run.
