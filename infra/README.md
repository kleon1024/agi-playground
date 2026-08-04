---
level: reference
---

# What does the machine underneath decide for you?

A platform chapter chooses the ML-side answer: which parallelism, which
quantization, how many rollouts. Every one of those choices is scored by
something below it — how the cards are wired, where the shards landed, who got
the slot, how the timing was measured. `infra/` is that layer, and its claim is
that the layer is teachable without a cluster: each chapter builds the mechanism
from scratch in `core/`, runs it on hardware you already have, and records the
numbers in `runs/`.

Each chapter names the platform chapter it is the substrate for, and that
platform chapter links back. If you arrived here from one of them, the return
link is at the top of the chapter. If you arrived from neither, the
[read-by-topic index](https://rehearse.maestro.onl/playground/topics/) lists
these chapters beside the platform and mission chapters that share their
question.

## Mechanism chapters

- [`01-networking/`](01-networking/) — star vs. ring allreduce topology,
  measured over real inter-process IPC: ring wins every combination tested
  and the margin widens with world size, plus the two deadlock bugs building
  the toy itself surfaced.
  Substrate for [`foundations/04-distributed-training/`](../foundations/04-distributed-training/).
- [`02-storage/`](02-storage/) — modulo vs. consistent-hash shard placement,
  measured by how much data actually moves on real disk when a storage node
  is added: 80% remapped vs. 18%, against a 20% theoretical floor.
  Substrate for [mission 01's corpus stage](../missions/01-language-model-agent/00-corpus/).
- [`03-orchestration/`](03-orchestration/) — a scheduler doesn't do more
  work, it decides whose work happens first: a real 10-job, 2-slot batch
  measured under FIFO vs priority dispatch, and the cold-start measurement
  artifact the first version of that comparison got wrong.
  Substrate for [`foundations/04-distributed-training/`](../foundations/04-distributed-training/).
- [`04-observability/`](04-observability/) — a real training loop
  (the language-model mission's `Transformer`, unmodified) instrumented with
  real per-step timing, and why p50/p95/histogram are different instruments
  than a mean.
  Substrate for [mission 01's evaluation stage](../missions/01-language-model-agent/07-eval/)
  and [the serving stage](../missions/01-language-model-agent/05-serve/).
- [`05-gpu-cluster-concepts/`](05-gpu-cluster-concepts/) — why interconnect
  topology (NVLink vs PCIe vs cross-node network) determines which
  parallelism strategy (data, tensor, pipeline) tolerates which link, and
  what part of that claim is measurable without a real cluster.
  Substrate for [`foundations/04-distributed-training/`](../foundations/04-distributed-training/).
- [`06-gpu-dedup-at-scale/`](06-gpu-dedup-at-scale/) — MinHash hashing cost
  stays flat per document, but LSH bucket verification does not: measured on
  CPU across four corpus sizes, verification overtakes hashing between
  16,000 and 48,000 synthetic documents, which is the real reason
  GPU-accelerated dedup (NeMo Curator-style) exists.
  Substrate for [mission 01's corpus stage](../missions/01-language-model-agent/00-corpus/).
- [`07-rollout-concurrency/`](07-rollout-concurrency/) — why lockstep
  rollout batching loses time to stragglers once trajectory length is
  heavy-tailed instead of fixed: measured across three worker-pool sizes,
  asynchronous scheduling beats lockstep by 1.73x at 2 workers, shrinking to
  1.30x at 8, which is the mechanism real asynchronous RLHF systems are
  built to avoid.
  Substrate for [mission 01's RL stage](../missions/01-language-model-agent/04-rl/).

## Compute lanes: where this repository's own runs happen

The chapters above teach general mechanism. The three documents below are
operational, and they describe two specific machines. Naming real hardware
belongs here and in `runs/` records, never in curriculum prose.

- [`local-4090.md`](local-4090.md) — **the default lane.** A Mac (or any) dev
  box reaching a Windows 11 host with an RTX 4090 over Tailscale, into WSL2
  Ubuntu. All `core/` toys, GPT-2-class pretraining, ≤8B LoRA SFT, GRPO on
  0.5–3B models, datatrove shards, and every inference, harness, and eval lab
  fit here. Full topology, setup checklist, smoke test, and pitfalls.
- [`modal.md`](modal.md) — **the cloud lane, multi-GPU labs only.** Reached
  only when a lesson genuinely needs more than one GPU. Every Modal lesson
  prints its dollar cost into `runs/`: there is no cloud spend without a
  visible number attached to it.
- [`tracking.md`](tracking.md) — Trackio as the default run tracker, the
  `runs/` metadata convention, and a filled `run.md` example. Applies to both
  lanes.

When a lesson's README doesn't say otherwise, assume the local lane.

| Workload class | Lane | Why |
|---|---|---|
| `core/` from-scratch toys (tokenizer, attention, tiny GRPO, nano-vLLM, harness) | Local | Small enough to run and iterate on interactively; no queueing, no cost |
| GPT-2-class pretraining (124M–350M params) | Local | Fits in 24GB with grad accumulation; hours-scale, not days |
| SFT / LoRA on models ≤8B | Local | LoRA keeps activation + optimizer memory small enough for one card |
| GRPO / RLVR on 0.5–3B models | Local | Comfortable with LoRA; matches the language-model mission's `04-rl` stage |
| datatrove data pipeline shards | Local (CPU-bound) | No GPU required |
| Inference, harness, and eval labs (nano-vLLM, agent loop, lm-eval/inspect-ai) | Local | Single-GPU serving is the whole point of the exercise |
| 2–4 GPU parallelism (FSDP2/TP/PP) | Modal | Requires multiple GPUs the local box doesn't have |
| 7B+ full-parameter SFT/RL | Modal | Exceeds single-card memory even with tricks |
| GPU-accelerated dedup at scale | Modal | Throughput work that benefits from elastic GPU count — [`06-gpu-dedup-at-scale/`](06-gpu-dedup-at-scale/) measures where the bottleneck shifts |
| RL rollout concurrency at scale | Modal | Needs parallel rollout workers beyond one card — [`07-rollout-concurrency/`](07-rollout-concurrency/) measures what lockstep costs |
