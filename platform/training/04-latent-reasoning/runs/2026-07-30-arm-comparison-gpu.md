# Run — direct/cot/latent arm comparison, completed on GPU

Follow-up to [`2026-07-30-arm-comparison.md`](2026-07-30-arm-comparison.md),
which ran the same command on CPU and only got through `direct` (and a
quarter-scale run of all three arms) before running out of session time. This
run uses the chapter's own full step budget, unmodified, on a GPU.

## Hardware and software

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4090, driver 591.86, reached over Tailscale (same box as this repo's serving/quantization/agent-harness runs) |
| Python / torch | remote `.venv` (uv), torch 2.13.0+cu130 |
| Model | 1,235,712 parameters, `d_model=128`, 6 layers (`core/model.py`) |
| Task | `core/task.py`, 40 entities, 4 hops, vocab 51 |
| Cost | \$0 (local lane over Tailscale, not a billed cloud run) |

## Command

```bash
cd stage-latent-reasoning   # core/model.py, task.py, train.py copied verbatim, no repo-relative imports
python3 train.py --arms direct cot latent --seeds 3 --out result.json --device cuda
```

Full budget, unmodified: `--steps 6000` for `direct`/`cot`, five
`--stage-steps 1500` curriculum stages for `latent` (7500 steps), 3 seeds
each.

## Result

Total wall-clock: 19.4 minutes for all nine runs (three arms x three seeds).

```
direct   mean 0.502   spread 0.012   wallclock ~82.5s/seed
cot      mean 0.9993  spread 0.002   wallclock ~82.9s/seed
latent   mean 0.502   spread 0.012   wallclock ~222.4s/seed
```

`direct` matches the earlier CPU-only partial run exactly (0.502, same seed
spread) — the same real finding, now on different hardware. `cot` resolves
cleanly: 0.9993 mean accuracy, essentially solving the task, decisively ahead
of `direct`. `latent` does not land between them as the chapter's hypothesis
predicted; it lands on `direct`, at chance.

## What the curriculum log explains

`latent`'s per-seed stage-by-stage accuracy (`result.json`'s `curriculum`
field) is the same shape across all three seeds:

```
n_latent=0   accuracy ~0.49-0.50   (no latent thoughts yet)
n_latent=1   accuracy ~0.50
n_latent=2   accuracy ~0.485-0.50
n_latent=3   accuracy 1.0          <- solves the task
n_latent=4   accuracy 0.50         <- the final stage, at the task's actual 4-hop depth
```

Every seed hits **1.0 accuracy at the `n_latent=3` stage**, then collapses to
**0.5 at `n_latent=4`** — the stage the curriculum was building toward, at
the reasoning depth the task actually requires. Final loss at `n_latent=4`
(0.345-0.353) matches `direct`'s converged loss almost exactly, meaning the
model is not merely failing to improve further — it is discarding whatever
let it solve the task at three latent steps and falling back to the same
degenerate solution `direct` finds directly. This is a specific, curriculum
transition failure, not a claim that latent reasoning cannot work at all: the
model demonstrably can use three latent thoughts productively.

## What this does and does not establish

- **Does establish**: `cot` beats `direct` decisively at this chapter's own
  step budget (0.9993 vs 0.502) — the half of the hypothesis the CPU run
  left open is now answered.
- **Does establish**: `latent` fails to land between `direct` and `cot` at
  this budget and curriculum shape; instead it collapses to `direct`'s
  solution exactly at the stage matching the task's true reasoning depth,
  after solving it at one stage earlier.
- **Does not establish**: that latent reasoning cannot work at this scale in
  general. A curriculum with a gentler final-stage transition (a shorter
  stage-steps ramp, or an intermediate `n_latent=3.5`-equivalent step), a
  wider latent channel, or a lower learning rate at the final stage are the
  next things to vary — none of them were tried here.

## Reproduce

```bash
# copy core/model.py, core/task.py, core/train.py to a GPU host (no repo-relative
# imports, so a flat directory is enough) and run:
python3 train.py --arms direct cot latent --seeds 3 --out result.json --device cuda
```
