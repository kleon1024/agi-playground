---
level: reference
---

# infra/ — compute lanes

agi-playground runs on two compute lanes. Every lesson states which lane it
targets; most of the curriculum lives on the local lane, and the cloud lane
is reserved for the handful of labs that genuinely need more than one GPU.

## The two-lane model

- **Local lane — RTX 4090 (24GB), default.** Reached from a Mac (or any)
  dev box over Tailscale SSH into a Windows 11 host running WSL2 Ubuntu.
  This is the default lane: all `core/` toys, GPT-2-class pretraining,
  ≤8B LoRA SFT, GRPO on 0.5–3B models, datatrove data shards, and every
  inference/harness/eval lab in the curriculum fit here. Free (you already
  own the hardware) and fully documented as its own lesson — remote dev
  over Tailscale is itself teachable content, not a footnote.
  See [`local-4090.md`](local-4090.md).
- **Cloud lane — Modal, multi-GPU labs only.** Used only when a lesson
  genuinely needs more than one GPU: 2–4 GPU FSDP2/TP/PP parallelism labs,
  7B+ full-parameter work, GPU-accelerated dedup at scale, and RL rollout
  concurrency. Every Modal lesson prints its dollar cost in `runs/` — there
  is no cloud spend without a visible number attached to it.
  See [`modal.md`](modal.md).
- **Tracking — Trackio by default, wandb optional**, for both lanes. See
  [`tracking.md`](tracking.md).

## Decision table: which lane for which workload

| Workload class | Lane | Why |
|---|---|---|
| `core/` from-scratch toys (tokenizer, attention, tiny GRPO, nano-vLLM, harness) | Local 4090 | Small enough to run and iterate on interactively; no queueing, no cost |
| GPT-2-class pretraining (124M–350M params) | Local 4090 | Fits in 24GB with grad accumulation; hours-scale, not days |
| SFT / LoRA on models ≤8B | Local 4090 | LoRA keeps activation + optimizer memory small enough for one card |
| GRPO / RLVR on 0.5–3B models | Local 4090 | Comfortable with LoRA; matches the speedrun's `04-rl` stage |
| datatrove data pipeline shards | Local 4090 (CPU-bound) | No GPU required; runs fine on the WSL2 box |
| Inference, harness, and eval labs (nano-vLLM, agent loop, lm-eval/inspect-ai) | Local 4090 | Single-GPU serving is the whole point of the exercise |
| 2–4 GPU parallelism (FSDP2/TP/PP) | Modal | Requires multiple GPUs the local box doesn't have |
| 7B+ full-parameter SFT/RL | Modal | Exceeds single-4090 memory even with tricks |
| GPU-accelerated dedup at scale (e.g. NeMo Curator-style) | Modal | Throughput work that benefits from elastic GPU count — see [`06-gpu-dedup-at-scale/`](06-gpu-dedup-at-scale/) for why the bottleneck shifts there in the first place |
| RL rollout concurrency at scale | Modal | Needs parallel rollout workers beyond one card |

When a lesson's README doesn't say otherwise, assume the local 4090 lane.

## Chapters

Alongside the operational runbooks below, `infra/` is growing a small set of
product-independent mechanism chapters — theory plus a from-scratch, CPU-
runnable `core/` and a real `runs/` entry, same contract as everywhere else
in this repository. These teach general infrastructure mechanism; the
runbooks below document this repository's own two real compute lanes.

- [`01-networking/`](01-networking/) — star vs. ring allreduce topology,
  measured over real inter-process IPC: ring wins every combination tested
  and the margin widens with world size, plus the two deadlock bugs building
  the toy itself surfaced.
- [`02-storage/`](02-storage/) — modulo vs. consistent-hash shard placement,
  measured by how much data actually moves on real disk when a storage node
  is added: 80% remapped vs. 18%, against a 20% theoretical floor.
- [`03-orchestration/`](03-orchestration/) — a scheduler doesn't do more
  work, it decides whose work happens first: a real 10-job, 2-slot batch
  measured under FIFO vs priority dispatch, and the cold-start measurement
  artifact the first version of that comparison got wrong.
- [`04-observability/`](04-observability/) — a real training loop
  (mission 01's `Transformer`, unmodified) instrumented with real per-step
  timing, and why p50/p95/histogram are different instruments than a mean.
- [`05-gpu-cluster-concepts/`](05-gpu-cluster-concepts/) — why interconnect
  topology (NVLink vs PCIe vs cross-node network) determines which
  parallelism strategy (data, tensor, pipeline) tolerates which link, and
  what part of that claim is measurable without a real cluster.
- [`06-gpu-dedup-at-scale/`](06-gpu-dedup-at-scale/) — MinHash hashing cost
  stays flat per document, but LSH bucket verification does not: measured on
  CPU across four corpus sizes, verification overtakes hashing between
  16,000 and 48,000 synthetic documents, which is the real reason
  GPU-accelerated dedup (NeMo Curator-style) exists.

## Setup docs

- [`local-4090.md`](local-4090.md) — Mac dev box → Tailscale → Windows 11 +
  RTX 4090 → WSL2 Ubuntu: full topology, setup checklist, smoke test, and
  common pitfalls.
- [`modal.md`](modal.md) — when to reach for Modal, a minimal `hello_gpu.py`
  pattern, Volumes for checkpoints, and cost/secrets handling.
- [`tracking.md`](tracking.md) — Trackio as the default run tracker, the
  `runs/` metadata convention, and a filled `run.md` example.
