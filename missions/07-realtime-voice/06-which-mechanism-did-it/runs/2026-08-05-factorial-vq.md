# The 2x2: dead-code reset crossed with EMA codebook update

## Commands

```bash
cd missions/07-realtime-voice/06-which-mechanism-did-it/core
uv run --group torch python train_factorial_codec.py --seed 0
uv run --group torch python train_factorial_codec.py --seed 1
uv run --group torch python train_factorial_codec.py --seed 2
```

Apple silicon laptop, macOS, CPU only. No CUDA GPU was available in this
environment — the same deviation from `mission.yaml`'s local-GPU-lane framing
that every real-speech stage in this mission records. Run 2026-08-05, the three
seeds launched concurrently. Per-seed wall-clock 4421.0s, 4415.1s, and 4429.4s
(73.7, 73.6, and 73.8 minutes) for all four arms plus dataset construction;
3.68 hours of process time in total, about 74 minutes of elapsed time because
the seeds ran side by side. \$0 marginal cost — the LibriSpeech `dev-clean`
archive was already cached from stage 03 and no new download was needed.

## The grid

Four arms per seed, run back to back inside one process:

| Arm | `dead_code_reset` | `ema_codebook` |
|---|---|---|
| `plain` | off | off |
| `reset-only` | on | off |
| `ema-only` | off | on |
| `reset+ema` | on | on |

Everything outside the quantizer is stage 04's setup, unchanged: the balanced
10-speaker LibriSpeech `dev-clean` mix from
[`04-multi-speaker/core/multi_speaker_data.py`](../../04-multi-speaker/core/multi_speaker_data.py),
400 training clips, 100 evaluation clips, 10 utterances per speaker, 2000 codec
steps, `lr=1e-3`, batch size 32, AdamW. `reset_every` 50 and `dead_threshold`
1.0 are stage 05's values, unchanged. `ema_decay` 0.99 with Laplace `epsilon`
1e-5 are van den Oord et al.'s defaults.

The dataset is built **once per seed** and shared by all four arms, and
`torch.manual_seed(seed)` runs immediately before each model is constructed, so
the four arms start from an identical encoder, decoder, and codebook.

## Two independent parity checks

**The `plain` corner must be stage 00's quantizer.** `arm_a_matches_stage_00`
builds stage 00's `VectorQuantizer` and the (off, off) `FactorialVectorQuantizer`
from the same seed, pushes the same input through both, and compares every
output tensor exactly. All three seeds: codebook initialization identical,
quantized output identical, tokens identical, commitment loss identical
(2.0149712562561035, 1.959599256515503, 2.0245676040649414 — reference and
candidate agreeing to the last bit).

**Two of the four corners are stages this mission already published**, and both
reproduce exactly rather than approximately:

| Seed | `plain` eval MSE | stage 04's | `reset-only` eval MSE | stage 05's |
|---|---|---|---|---|
| 0 | 0.027124574407935143 | 0.027124574407935143 | 0.01874581165611744 | 0.01874581165611744 |
| 1 | 0.016980957239866257 | 0.016980957239866257 | 0.017170587554574013 | 0.017170587554574013 |
| 2 | 0.0212225541472435 | 0.0212225541472435 | 0.01733442209661007 | 0.01733442209661007 |

Codebook usage and entropy ratio match to full float precision as well, and so
do the reset counts (1893, 1848, 1388). The two new corners are therefore
measured against the mission's own published baselines, not against a
re-implementation that happens to be close.

## Results

Baselines per seed (silence / mean-signal reconstruction MSE on the eval split):
seed 0 — 0.028330 / 0.028404; seed 1 — 0.027497 / 0.027575; seed 2 — 0.027463 /
0.027538.

| Seed | Arm | Codes used | Entropy ratio | Eval MSE | Margin vs silence | Resets | Reset events (of 40) |
|---|---|---|---|---|---|---|---|
| 0 | `plain` | 18 / 64 | 0.4051 | 0.02712 | 4.3% | 0 | 0 |
| 0 | `reset-only` | 64 / 64 | 0.8256 | 0.01875 | 33.8% | 1893 | 38 |
| 0 | `ema-only` | 1 / 64 | 0.0000 | 0.02834 | −0.0% | 0 | 0 |
| 0 | `reset+ema` | 64 / 64 | 0.9332 | 0.01810 | 36.1% | 435 | 12 |
| 1 | `plain` | 63 / 64 | 0.7598 | 0.01698 | 38.2% | 0 | 0 |
| 1 | `reset-only` | 64 / 64 | 0.8141 | 0.01717 | 37.6% | 1848 | 38 |
| 1 | `ema-only` | 1 / 64 | 0.0000 | 0.02751 | −0.0% | 0 | 0 |
| 1 | `reset+ema` | 64 / 64 | 0.8723 | 0.01679 | 38.9% | 1670 | 30 |
| 2 | `plain` | 32 / 64 | 0.6436 | 0.02122 | 22.7% | 0 | 0 |
| 2 | `reset-only` | 64 / 64 | 0.7910 | 0.01733 | 36.9% | 1388 | 31 |
| 2 | `ema-only` | 1 / 64 | 0.0000 | 0.02747 | −0.0% | 0 | 0 |
| 2 | `reset+ema` | 62 / 64 | 0.8748 | 0.02051 | 25.3% | 2132 | 38 |

`ema-only`'s eval MSE lands one part in ten thousand *above* the silence
baseline on every seed (0.02834 vs 0.02833, 0.02751 vs 0.02750, 0.02747 vs
0.02746). It is the only arm in this mission that fails `mission.yaml`'s
"beats a naive baseline" acceptance criterion, and it fails it on all three
seeds. Its training history shows the collapse is immediate: reconstruction
loss is already at silence level by step 100 and never leaves.

## Main effects, each measured twice

Each mechanism's effect is the difference between two arms that differ in that
mechanism alone — computed once with the other switch off and once with it on.

| Seed | Effect | d codes | d entropy | d eval MSE |
|---|---|---|---|---|
| 0 | reset, without EMA | +46 | +0.4205 | −0.00838 |
| 0 | reset, with EMA | +63 | +0.9332 | −0.01024 |
| 0 | EMA, without reset | −17 | −0.4051 | +0.00122 |
| 0 | EMA, with reset | +0 | +0.1077 | −0.00065 |
| 1 | reset, without EMA | +1 | +0.0543 | +0.00019 |
| 1 | reset, with EMA | +63 | +0.8723 | −0.01071 |
| 1 | EMA, without reset | −62 | −0.7598 | +0.01052 |
| 1 | EMA, with reset | +0 | +0.0582 | −0.00038 |
| 2 | reset, without EMA | +32 | +0.1474 | −0.00389 |
| 2 | reset, with EMA | +61 | +0.8748 | −0.00696 |
| 2 | EMA, without reset | −31 | −0.6436 | +0.00625 |
| 2 | EMA, with reset | −2 | +0.0838 | +0.00318 |

The EMA rows change sign between the two levels of reset on every seed and on
every metric: entropy ratio moves −0.41/−0.76/−0.64 without reset and
+0.11/+0.06/+0.08 with it. That is the interaction, and it is what makes a
single "EMA effect" number meaningless here.

## Reset behaviour under EMA

`n_reset_events` counts how many of the 40 checkpoints (one per 50 steps) found
at least one dead code.

| Seed | `reset-only` events / total resets | `reset+ema` events / total resets |
|---|---|---|
| 0 | 38 / 1893 | 12 / 435 |
| 1 | 38 / 1848 | 30 / 1670 |
| 2 | 31 / 1388 | 38 / 2132 |

On seed 0 the EMA codebook stops going dead early and reset fires on only 12 of
40 checkpoints. On seed 1 the reduction is smaller, and on seed 2 reset fires
*more* often with EMA than without. One seed of three shows the stabilization;
the other two do not, so this is a single observation and not a pattern.

## Per-speaker spread on the eval split

Ten speakers, mean MSE per speaker, best to worst:

| Seed | `reset-only` | `reset+ema` |
|---|---|---|
| 0 | 0.01174 – 0.02778 | 0.01042 – 0.02656 |
| 1 | 0.01108 – 0.02218 | 0.01083 – 0.02087 |
| 2 | 0.01271 – 0.02355 | 0.01327 – 0.03055 |

Same ordering as the aggregate: `reset+ema` is better at both ends on seeds 0
and 1 and worse at both ends on seed 2.

## Trainable-tensor accounting

The EMA arms report 28 trainable tensors against the gradient arms' 29 — the
codebook embedding is excluded from the optimizer, which is the check that the
EMA rule is the only thing writing to it. `codebook_is_gradient_trained` is
`False` on both EMA arms and `True` on both gradient arms, recorded per arm in
the JSON.

## Raw records

[`factorial-codec-seed0.json`](factorial-codec-seed0.json),
[`factorial-codec-seed1.json`](factorial-codec-seed1.json),
[`factorial-codec-seed2.json`](factorial-codec-seed2.json) — per-arm training
history, codebook usage, per-speaker MSE, reset counts, the computed main
effects, and the stage 00 parity check.
