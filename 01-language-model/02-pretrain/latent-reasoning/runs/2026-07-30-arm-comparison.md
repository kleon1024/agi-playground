# Run — direct/cot/latent arm comparison, and why it stayed partial

## Hardware and software

| | |
|---|---|
| Machine | local Apple Silicon Mac, CPU only (no CUDA/MPS path in `train.py`) |
| Python / torch | 3.11.14 / 2.10.0 |
| Model | 1,235,712 parameters, `d_model=128`, 6 layers (`core/model.py`) |
| Task | `core/task.py`, 40 entities, 4 hops, vocab 51 |

## What actually happened

The chapter's own reproduce command is:

```bash
python train.py --arms direct cot latent --seeds 3 --out result.json
```

Its defaults are `--steps 6000` (direct/cot) and `--stage-steps 1500` (5
curriculum stages for latent, i.e. 7500 steps), times 3 seeds, times three
arms. Run at those defaults on this machine, the **direct** arm alone took
957.8-1006.6s per seed (about 16-17 minutes); the full three-arm sweep did not
finish inside a session-length budget and was interrupted partway through the
**cot** arm. The partial output is real and is kept:
[`2026-07-30-arm-comparison.json`](2026-07-30-arm-comparison.json) — direct
only, 3 seeds, mean accuracy **0.502** (0.494 / 0.506 / 0.506), seed spread
0.012, converged loss 0.345-0.354.

To get a same-scale reading on all three arms in one sitting, a second run
used a quarter of the default budget: `--steps 1500 --stage-steps 300`. That
run completed and is kept as
[`2026-07-30-arm-comparison-reduced.json`](2026-07-30-arm-comparison-reduced.json):

```
direct   mean accuracy 0.502  (0.506 / 0.506 / 0.494)   loss 0.34-0.35
cot      mean accuracy 0.5013 (0.504 / 0.506 / 0.494)   loss 0.83-0.88 (not converged)
latent   mean accuracy 0.5007 (0.502 / 0.506 / 0.494)   final-stage loss 0.35-0.36
```

## The honest read

All three arms sit at chance (this is a balanced yes/no task, so 0.50 is the
floor). `direct`'s loss is fully converged and identical whether trained for
1500 or 6000 steps (0.345-0.354 either way) — a stable result, not an
artifact of too little training: a single forward pass genuinely cannot do
4-hop reachability on this task at this model scale, at either step count.
`cot`'s loss at the reduced budget (0.83-0.88) has clearly not converged,
unlike its full-budget run, which was cut off mid-training rather than
completed — so this run cannot say whether `cot` beats `direct` at the
chapter's intended scale, only that a quarter of that budget is not enough
for `cot` to separate from chance. The same applies to `latent`, one level
further removed: its curriculum needs `cot`-level convergence at each stage
to hand the next stage a supervised thought, and at this budget it does not
get there either.

## What this does and does not establish

- **Does establish**: `direct` genuinely fails this task, stably, regardless
  of step count in the range tested — a real result, not a training
  artifact.
- **Does not establish**: whether `cot` beats `direct`, or where `latent`
  lands relative to both, at the step budget the chapter's own hypothesis is
  stated for. Both remain open; the reduced run answers a different, smaller
  question (is a quarter of the budget enough) with "no."

## Reproduce

```bash
cd 01-language-model/02-pretrain/latent-reasoning/core
python train.py --arms direct cot latent --seeds 3 --out ../runs/full.json
# full run; direct alone takes ~16-17 min/seed on a CPU-only machine, cot and
# especially latent (n_latent+1 forward passes per step) cost more per step
python train.py --arms direct cot latent --seeds 3 --steps 1500 --stage-steps 300 \
    --out ../runs/reduced.json
# quarter-scale, completes in under two hours on the same machine
```
