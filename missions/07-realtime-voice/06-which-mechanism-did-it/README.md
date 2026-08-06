---
status: verified
level: applied
base: scratch
verified: 2026-08-05
label: Which mechanism did it
---

# Stage 05 refused to run two mechanisms at once. What does running all four combinations show?

Stage 05 tested dead-code reset on its own and said why it stopped there:
adding EMA-updated codebook embeddings on top "would confound which mechanism
did the work." That reasoning is correct for a two-arm comparison. Run the
reset arm against the reset-plus-EMA arm and a win belongs to the pair, exactly
as it would have belonged to the pair in stage 04's baseline.

It stops being correct the moment all four combinations exist. With reset set
`off`/`on` crossed against EMA set `off`/`on`, each mechanism's effect is the
difference between two cells that differ in that mechanism alone — measured
twice, once at each level of the other switch. Nothing is confounded, because
nothing moves except the switch under test.

This stage runs that 2x2. The answer turns out to depend on which half of the
grid you read, which is precisely the situation a two-arm experiment cannot
detect.

**Before this:** [stage 05](../05-codebook-reset/), which found dead-code reset
takes all three seeds to 64 of 64 codes used, and named the untested EMA half
as the open question.

## Two switches that do different jobs

They can be crossed at all because they are not alternatives:

- **Dead-code reset** changes *which* codebook entries exist. Every 50 steps,
  any entry whose EMA usage count has fallen below 1.0 is reinitialized to a
  random encoder output from the current batch. It rescues entries the encoder
  has abandoned.
- **EMA codebook update** changes *how* the surviving entries move. Instead of
  the optimizer pulling `codebook.weight` toward the encoder outputs through
  the commitment loss, each entry becomes a decayed running average of the
  encoder outputs currently assigned to it — van den Oord et al.'s original
  alternative to the gradient update, carried into VQ-VAE-2.

Reset decides membership; EMA decides position. Everything else — encoder,
decoder, dataset, the balanced 10-speaker LibriSpeech mix, 2000 steps,
`lr=1e-3`, batch size 32, the three seeds — is stage 04's setup, unchanged.

## The grid

Eval MSE against the silence baseline, 100 held-out clips, per seed:

| Arm | Codes used | Entropy ratio | Margin over silence |
|---|---|---|---|
| `plain` | 18, 63, 32 / 64 | 0.405, 0.760, 0.644 | 4.3%, 38.2%, 22.7% |
| `reset-only` | 64, 64, 64 / 64 | 0.826, 0.814, 0.791 | 33.8%, 37.6%, 36.9% |
| `ema-only` | 1, 1, 1 / 64 | 0.000, 0.000, 0.000 | −0.0%, −0.0%, −0.0% |
| `reset+ema` | 64, 64, 62 / 64 | 0.933, 0.872, 0.875 | 36.1%, 38.9%, 25.3% |

Read the `ema-only` row first. EMA alone does not merely underperform — it
collapses the codebook to a single entry on every seed, and the reconstruction
lands one part in ten thousand *worse* than reproducing silence. It is the only
arm anywhere in this mission that fails `mission.yaml`'s own "beats a naive
baseline" acceptance bar, and it fails it three times out of three.

Then read `reset+ema`. Entropy ratio rises above `reset-only` on every seed —
0.933 vs 0.826, 0.872 vs 0.814, 0.875 vs 0.791. The codebook is not just fully
occupied, it is used more evenly.

## The sign flip

Put those two rows together and EMA's measured effect is:

| EMA's effect on entropy ratio | seed 0 | seed 1 | seed 2 |
|---|---|---|---|
| without reset (`ema-only` − `plain`) | −0.405 | −0.760 | −0.644 |
| with reset (`reset+ema` − `reset-only`) | +0.108 | +0.058 | +0.084 |

Same mechanism, same code path, opposite sign, on all three seeds. There is no
"the EMA effect" to report. A two-arm study that had tested EMA against the
plain baseline would have concluded EMA destroys the codec; one that had tested
`reset+ema` against `reset-only` would have concluded EMA helps. Both would
have been reporting a real measurement, and both would have been wrong about
the mechanism.

## Why the collapse happens, and why reset stops it

The two rows are consistent with one story about dead codes. Under the EMA
rule, an entry that stops being selected receives nothing: its running sum is
multiplied by the decay every step and nothing is added, while the Laplace
smoothing keeps its denominator at a small positive floor. The entry drifts
toward the origin, and so does every other unselected entry — they pile up in
the same place, where none of them wins an assignment again. A gradient-trained
codebook is not immune to dead codes (that is stage 04's whole finding), but
the optimizer's momentum keeps abandoned entries wandering rather than
converging on a common point.

Reset is the missing revival path. It reinitializes a dead entry to a live
encoder output, which is somewhere the encoder actually sends things, and the
EMA rule then holds it there — which is the part the gradient update does less
firmly. That division of labour is what the entropy gain in `reset+ema` looks
like from the inside, and it is why the practical VQ-VAE literature pairs the
two rather than choosing between them.

One seed shows this directly. Dead-code reset fires on 38 of 40 checkpoints in
`reset-only` on seed 0, and on only 12 of 40 in `reset+ema` — codes stop dying
once EMA holds them. Seed 1 shows a smaller reduction (30 of 40) and seed 2
shows the opposite (38 of 40, more than `reset-only`'s 31). One seed of three
is an observation, not a pattern, and this stage does not claim otherwise.

## What EMA does not buy

Reconstruction quality does not follow entropy. `reset+ema` beats `reset-only`
on seeds 0 and 1 (36.1% vs 33.8%, 38.9% vs 37.6% margin over silence) and loses
badly on seed 2 (25.3% vs 36.9%). That seed also ran the most resets of any arm
in the grid — 2132, against `reset-only`'s 1388 — so its codebook was still
churning at the end of training rather than settling.

A more uniformly used codebook is not automatically a better codec. Stage 05
already drew that distinction when it said reset "eliminates *dead* codes, not
that it produces a perfectly uniform codebook"; this stage supplies the other
half, which is that pushing uniformity further does not reliably buy quality.
Across three seeds, EMA's quality effect on top of reset spans −0.00065 to
+0.00318 in MSE and contains zero. On this evidence it is not a result.

## The check that makes the comparison legitimate

Two of the four corners are stages this mission already published, so they can
be verified rather than assumed. `plain` reproduces stage 04 and `reset-only`
reproduces stage 05 — not to three decimals, but to the full float:
0.027124574407935143 and 0.01874581165611744 on seed 0, and identically on the
other two seeds, with the same codebook usage, the same entropy ratios, and the
same reset counts (1893, 1848, 1388).

Separately, the `plain` quantizer is checked against stage 00's original
`VectorQuantizer` by forward pass rather than by reading the code: same seed,
same input, and codebook initialization, quantized output, tokens, and
commitment loss all compared exactly. All four identical on all three seeds.

Without those checks the two new corners would be measured against a
re-implementation that merely resembles the mission's baseline. With them, the
grid is four cells of one experiment.

## What ran

```bash
cd missions/07-realtime-voice/06-which-mechanism-did-it/core
uv run --group torch python train_factorial_codec.py --seed 0
uv run --group torch python train_factorial_codec.py --seed 1
uv run --group torch python train_factorial_codec.py --seed 2
```

Apple silicon laptop, CPU only — the same deviation from `mission.yaml`'s
local-GPU-lane framing every real-speech stage here records. 2026-08-05, three
seeds concurrent, about 74 minutes each for all four arms, 3.68 hours of
process time in total, \$0 marginal cost on the already-cached LibriSpeech
archive. Full numbers in
[`runs/2026-08-05-factorial-vq.md`](runs/2026-08-05-factorial-vq.md).

## What this stage does not establish

Nothing about `ema_decay` or `epsilon` beyond the single values tried (0.99 and
1e-5), and nothing about `reset_every` or `dead_threshold` beyond stage 05's
50 and 1.0 — a 2x2 over two switches is not a sweep over four hyperparameters,
and `ema-only`'s collapse is a statement about EMA at this decay and this step
count, not about EMA in general. Three seeds, still 10 of `dev-clean`'s 40+
speakers, still 2000 steps.

The quality effect of EMA on top of reset is inconclusive, and this stage says
so rather than picking the two seeds that agree. No third mechanism was
crossed in: VQ-VAE-2's hierarchy of codebooks, residual quantization, and
codebook regularization are all absent. And the KV-cache streaming path was not
re-run, for stage 05's reason — stages 01, 03, and 04 established it is
indifferent to codec internals, so re-running it would test nothing new.

## Check your mental model

1. `ema-only` collapses to 1 of 64 codes and `reset+ema` reaches 64 of 64 with
   the highest entropy in the grid. Why is "EMA is bad but reset rescues it"
   not quite the right reading?

<details>
<summary>Answer</summary>

Because it treats EMA as a thing with a fixed quality that reset compensates
for, when the measurement shows EMA doing two different jobs depending on what
else is running. Alone, EMA has no way to revive an abandoned entry, so its
update rule is a liability. With reset supplying revivals, the same rule
becomes the reason revived entries stay put — `reset+ema` has higher entropy
than `reset-only` on every seed, which is EMA contributing something reset
alone does not. The honest statement is about the pair: reset provides
membership, EMA provides stability, and neither claim survives being made about
one mechanism in isolation.

</details>

2. Stage 05 declined to test EMA on the grounds that it would confound two
   mechanisms. Adding EMA is exactly what this stage did. Why is that not the
   same mistake?

<details>
<summary>Answer</summary>

Stage 05 would have compared `reset-only` against `reset+ema` and called the
difference "the fix". That comparison is fine — it is one of the four
differences computed here — but on its own it cannot tell you whether the
result came from reset, from EMA, or from the two interacting, because the
`ema-only` cell needed to separate them would not exist. What confounds an
experiment is a missing cell, not an extra mechanism. Adding the fourth arm
turns the same two mechanisms from a confound into two measured effects, each
computed twice. Stage 05's caution was right about its own design and wrong as
a general rule.

</details>

3. `reset+ema` has the highest entropy ratio in the grid on every seed, yet
   loses to `reset-only` on reconstruction on seed 2. What does that say about
   using codebook entropy as the thing to optimize?

<details>
<summary>Answer</summary>

That it is a diagnostic, not an objective. Entropy ratio measures how evenly
the codebook is used, which is a good detector of the specific failure this
mission has hit repeatedly — a codec that has quietly stopped using most of its
vocabulary. It is not a measure of whether the tokens carry the waveform well.
Seed 2 has near-total, evenly spread codebook occupancy and worse
reconstruction than the arm with lower entropy, because it was still resetting
codes heavily at step 2000 and never settled. Optimizing entropy directly would
reward exactly that churn. The reconstruction metric stays the one the mission
accepts on; entropy stays the instrument that explains why it moved.

</details>

## Next

This closes the mechanism question `mission.yaml`'s `does_not_prove` left open
after stage 05. The open boundary is now hyperparameters and scale rather than
mechanism identity: no sweep over the decay, the reset period, or the dead
threshold, and still 10 speakers. Return to [the mission report](../02-report/)
for what the whole chain does and does not license you to claim.

Primary references: van den Oord, Vinyals & Kavukcuoglu, *Neural Discrete
Representation Learning* (NeurIPS 2017), for the EMA codebook update; Razavi,
van den Oord & Vinyals, *Generating Diverse High-Fidelity Images with VQ-VAE-2*
(NeurIPS 2019), for the dead-code reset this stage crosses it with.

A detour from here: [which half of the fix did the work?](the-half-that-did-the-work/)
— the 2x2 grid read across three seeds: the reset carried the work
(EMA-only is worse than plain in every seed), and EMA only enhances when
the reset is present.

Another detour: [the 2x2 is trustworthy because its corners are already published](when-the-corners-reproduce/) — the recorded grid read: plain and reset-only reproduce stage 04/05 bit-for-bit, and the ema-only corner shows the EMA is not the fix.
