# Run tracking

Every lesson's `runs/` directory is the honesty mechanism for this repo: a
lesson without a verified, tracked run is marked `status: draft` and
excluded from the curriculum map. This document covers the tracking tool
and the `runs/` metadata convention that makes that verification checkable.

## Trackio as the default

[Trackio](https://github.com/gradio-app/trackio) is the default experiment
tracker for both compute lanes (local 4090 and Modal). Two reasons it's the
default rather than an afterthought:

- **Local-first.** Trackio runs and stores data locally by default, which
  matches the local-4090-as-default-lane posture of this repo — no
  external account or network dependency required just to log a training
  curve.
- **Source readable in one sitting.** Trackio's codebase is small enough
  to actually read end-to-end, which matches this repo's pedagogy of
  pairing a minimal, readable implementation with the production tool it
  mirrors (here: Trackio ↔ wandb, the same "read the toy, then map to the
  real thing" pattern used everywhere else in the curriculum).

Trackio is designed as a drop-in for the wandb API: most code needs only

```python
import trackio as wandb
```

in place of `import wandb`, and the rest of the logging calls
(`wandb.init(...)`, `wandb.log(...)`, etc.) work unchanged.

**wandb is optional.** Lessons may use real wandb instead where a learner
wants the production experience directly, but Trackio is what the repo's
own examples default to.

## `runs/` metadata convention

Each run directory under a lesson's `runs/` contains a `run.md` recording
exactly what was run, on what hardware, and what it produced:

- **Exact command** — the literal command line invoked, so the run is
  reproducible verbatim.
- **Config** — the hyperparameters/config values in effect for that run
  (inline, or a path to the config file used).
- **Hardware** — which compute lane and specific hardware (e.g. "local
  RTX 4090" or "Modal, 4x A100-40GB").
- **Wall-clock** — how long the run actually took.
- **Cost** — dollar cost, required whenever the run used the Modal lane
  (see [`modal.md`](modal.md)'s cost-printing rule); `$0` (local hardware
  already owned) for the local lane.
- **Metrics** — the run's results: final/curve metrics, loss values,
  eval scores, or a link to the Trackio export that has the full curve.

### Filled example

```markdown
# Run: 02-pretrain, 3.0B tokens

- **Command:** `python train.py --data data/tokens --out ckpt --tokens 3.0e9 --compile`
- **Config:** 88,197,888 params (12 layers, d=768, 12 Q heads / 4 KV heads,
  SwiGLU d_ff=2048, RMSNorm, RoPE), bf16, micro-batch 16 x grad_accum 8
- **Hardware:** local RTX 4090 (24GB), WSL2, driver 591.86
- **Wall-clock:** 4.98h
- **Cost:** \$0 (local hardware)
- **Metrics:** best val loss 3.0689 at step 21,000, final 3.0984; 167.2k tok/s,
  65.1% MFU, 9.05GB peak; curve in `runs/2026-07-28-pretrain-3b.md`
```

Those are the real numbers from
`missions/01-language-model-agent/02-pretrain/runs/2026-07-28-pretrain-3b.md`,
and the example uses them for the same reason the rest of the repository does:
an illustration that is indistinguishable from a record should not contain
figures nobody measured.

A `run.md` missing any of these fields is incomplete — treat it the same
as a missing run for the purposes of a lesson's `status: draft`/verified
gate.
