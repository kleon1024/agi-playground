---
status: verified
verified: 2026-07-24
---

# Cloud lane — Modal

Modal is the second compute lane: reach for it only when a lesson genuinely
needs more than the local RTX 4090 can offer. Everything else in the
curriculum stays on [`local-4090.md`](local-4090.md).

> **Status: verified 2026-07-24.** The `hello_gpu.py` below was run as-is
> with `modal run hello_gpu.py` on an A10 (Modal substituted `A10` for the
> requested `A10G` class). Output:
>
> ```
> NVIDIA A10 | capability (8, 6)
> ```
>
> Wall clock ≈2 minutes including the one-time image build (torch install);
> the warm GPU portion was seconds. Compute cost: on the order of a cent —
> A10 is ~\$1.10/hr billed per-second. Per the cost-printing rule, real
> lessons must report their exact dollar cost from the Modal dashboard.

## When to use Modal

Use the Modal lane for workload classes that outgrow one GPU:

- **2–4 GPU parallelism labs** — FSDP2, tensor parallelism (TP), pipeline
  parallelism (PP) exercises that require multiple GPUs to be meaningful.
- **7B+ full-parameter RL or SFT** — beyond what a single 24GB card can
  hold without LoRA or heavy offloading.
- **GPU-accelerated dedup at scale** — throughput-bound data-processing
  work that benefits from elastic GPU count rather than a fixed local card.
- **RL rollout concurrency** — labs that need many parallel rollout workers
  to demonstrate throughput/scaling behavior that a single machine can't.

If a lesson fits on the local 4090, it stays there — Modal is for the
exceptions, and every exception prints its cost (see below).

## Minimal pattern: `hello_gpu.py`

This is the smallest end-to-end Modal program in the curriculum: it
provisions a GPU-backed container, imports PyTorch inside it, and returns
the GPU's name and compute capability back to the caller.

```python
import modal

app = modal.App("agi-playground-hello")
image = modal.Image.debian_slim().pip_install("torch")


@app.function(gpu="A10G", image=image, timeout=300)
def hello() -> str:
    import torch

    return f"{torch.cuda.get_device_name(0)} | capability {torch.cuda.get_device_capability(0)}"


@app.local_entrypoint()
def main():
    print(hello.remote())
```

- `modal.App` names the application; `modal.Image` builds the container
  image declaratively (here: Debian slim + `torch` via pip).
- `@app.function(gpu=..., image=..., timeout=...)` is the unit of remote
  compute — it runs the decorated function inside a container with the
  requested GPU attached.
- `@app.local_entrypoint()` marks the function that runs locally and
  dispatches to Modal via `.remote()`.
- Later labs in `06-inference` and `05-rl` swap `gpu="A10G"` for the
  multi-GPU configurations (e.g. `gpu="A100:4"`-style specs) that the
  parallelism exercises actually need — this file is the template they
  start from.

## Volumes for checkpoints

Modal `modal.Volume` objects are the persistence mechanism for anything
that needs to survive across container runs — model checkpoints, dataset
shards staged for a run, or intermediate artifacts. Attach a volume to a
function so checkpoints written inside the container land in durable
storage rather than disappearing when the container exits, and so a
later function invocation (e.g. a resume-from-checkpoint step) can read
what a previous one wrote.

## Cost-printing rule

Every `runs/` entry produced by a Modal lesson **states its dollar cost**.
Modal bills by container GPU-seconds; the `run.md` for a Modal-lane run
must record the observed run duration and the resulting cost alongside the
usual command/config/metrics fields (see [`tracking.md`](tracking.md) for
the full schema). No Modal lesson ships without a visible number attached
to what it cost to produce.

## Secrets handling

Use **Modal secrets** for any credential a Modal function needs (API keys,
tokens, cloud storage credentials). Create them via the Modal dashboard or
CLI and reference them in the function decorator (`secrets=[...]`) — they
are injected as environment variables inside the container at run time.
Secrets are never committed to the repo, never hardcoded in `hello_gpu.py`-
style scripts, and never passed as plain function arguments.
