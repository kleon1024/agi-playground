---
status: verified
level: applied
base: none
label: When the curve goes wrong
verified: 2026-08-07
---

# The loss curve looks wrong. Which subsystem owns it?

This mission's own pretraining run ended badly and nobody knows why. Validation
loss reached its best value of **3.0689 at step 21,000**, then rose to
**3.0984** by step 22,500 — the final 6.5% of a five-hour budget went the wrong
way. [Verifying the run](../verifying-the-run/#what-five-hours-bought) names
three explanations that all fit the same curve, and says one run cannot
distinguish them.

That is the situation this chapter is about. A curve is a symptom, and every
symptom has several subsystems that could have produced it. What you need is
not a guess about which one it is; it is a rule for deciding which subsystem
owns the evidence, so the next thing you measure can rule something out.

**Before this:** [how do you know a five-hour run is working?](../verifying-the-run/),
for this run's actual loss curve, its MFU, and its schedule. Everything below
assumes you have that curve in front of you.

## Read the pair, not the line

Training loss alone cannot distinguish a model that is learning too well from a
loop that is not learning at all. The pair of training and held-out loss can:

| Observation | First hypothesis |
|---|---|
| both flat | label shift, masking, optimizer, or learning rate |
| train falls, held-out flat | overfitting, or a train/held-out mismatch |
| both fall, then spike | instability, a bad batch, overflow, or a resume defect |
| periodic jumps | data shards, schedule boundaries, or checkpoint restore |
| smooth loss, poor samples | tokenizer, data distribution, or evaluation mismatch |

These rows are now executed, not asserted. A from-scratch 2-layer
next-token learner ([record](runs/2026-08-07-curve-diagnosis.md)) gets
four planted failures, and each produces its row: a too-high learning
rate spikes both curves with no recovery (row three, instability), and
its gradient-norm trace departs from the baseline run two steps before
the loss does; a corrupted batch moves train and held-out together and
both return toward the baseline path (row three, bad batch); a bf16
master weight flattens both curves while the gradient norm stays alive
(row one, flat-flat); and a softmax that overflows the compute range
goes non-finite at a specific step (row three, overflow).

The value of the table is that each row names a *different owner*. Do not go
from a bad sample straight to a bigger model — identify which subsystem the
evidence belongs to first, because the fix for a label-shift bug and the fix
for an overfit model have nothing in common.

The 3.0689-to-3.0984 rise above is row three read carefully: both losses fell,
then one turned. Its three candidate owners are the data (approaching one full
epoch), the schedule (a cosine floor too high to settle into), and the
measurement itself (each point samples the held-out set rather than consuming
it). Ruling any of them out takes paired runs across seeds, which is what
[the ablation harness](../../../foundations/05-is-the-difference-real/) is for.

## When the arithmetic is the owner

Row three's "overflow" is the one people skip, because the run appears to work
until it doesn't. Reduced precision is not a single property, and the two
16-bit formats fail in opposite directions.

Change the format below and read the two axes apart: how large a number can be
represented at all, and how finely numbers near a given magnitude can be told
apart.

<!-- interactive: PrecisionFormats -->

BF16 keeps FP32's exponent range, so it does not need FP16's loss-scaling
machinery to avoid overflow — that is why this run trains in it. What BF16
gives up is mantissa bits, and that loss lands in a specific place: an
optimizer update is usually a small correction added to a much larger
accumulated value, and in reduced mantissa precision a small enough correction
rounds away against a large enough accumulator. The update does not error. It
simply does not happen.

So the contract is mixed, not uniform:

```text
bf16   activations and matrix multiplies
fp32   accumulation, optimizer state, the authoritative weight update
always explicit checks for non-finite loss and gradients
```

Lower precision buys memory and bandwidth. It does not make numerical
validation optional — and a run without the non-finite checks cannot even
report which step first went wrong.

Both halves are measured in the same run. With bf16 master weights, the
planted learner's train curve flatlines at 2.418 while the fp32-master
control keeps descending to 2.358 — and the gradient norm stays alive at
0.050, which is what rules out a dead loop. And the overflow run's loss
goes non-finite at step 3: with the check the run stops and reports that
step; without it, the run completes with a wall of inf then NaN and no
step attribution.

## When you extend the run instead of fixing it

Once the curve is understood, the next temptation is to keep going: more
tokens, longer context, a domain the base corpus barely covered. Each of those
changes what the curve means, so each needs its own record.

Longer context changes memory, data, and position use at once. RoPE scaling
methods make longer positions representable, but representable is not trained —
they do not create long-range examples in a corpus that has none. Continued
pretraining changes the data distribution, which risks erasing what the base
run bought. Four rules keep that honest:

- begin near the base run's *final* learning rate, not its original peak;
- mix general replay data whenever general capability must be preserved;
- evaluate domain gain and general regression together, in the same report;
- version the new mixture separately from the base corpus.

The comparison is two-objective on purpose. A continued run that gains the
target domain while silently losing the baseline has not improved the model; it
has traded one capability for another without saying so.

## What this chapter does not establish

Nothing here diagnosed this run's own anomaly. The 3.0689-to-3.0984 rise is
still unattributed, and the reason is structural rather than a missing
paragraph: it is one run at one seed, and each of its three candidate owners
predicts the same curve. The precision contract above is stated from the
formats' definitions, not measured — this repository has not trained the same
configuration in FP16 to watch it overflow, and it has not run a continued
pretraining pass at all, so the four rules are published practice rather than
this mission's evidence. The injected-failure run executes the diagnostic
procedure on a 2-layer toy, not the 88M decoder: its LR values are knobs
chosen to make each failure visible, its bf16 column simulates a bf16
master weight rather than the full fp32-master contract, and its overflow
threshold (fp32-range softmax without max subtraction) is not this run's
format. What transfers is the pair-reading rule and the telemetry
discipline, not the specific numbers.

Primary references: Micikevicius et al., *Mixed Precision Training* (2018) for
the FP32 master-weight contract; Gururangan et al., *Don't Stop Pretraining*
(2020) for continued-pretraining evaluation; Peng et al., *YaRN* (2023) for
context extension.

## The fix and its trade

The failure this chapter treats is the unattributed curve: validation loss
reached its best 3.0689 at step 21,000, then rose to 3.0984 by step 22,500,
and three subsystems can each explain it — data approaching one full epoch,
a cosine floor too high to settle into, or evaluation noise from sampling
the held-out set. One run at one seed cannot distinguish them, and that is
the structural reason this chapter's own anomaly stays unattributed: the
fix is not a guess about which one it is, it is a rule for deciding which
subsystem owns the evidence. The pair-reading table is that rule — both
flat points at the loop (label shift, masking, optimizer, learning rate),
train-falls-held-out-flat at overfitting or a split mismatch, both-fall-
then-spike at instability or a bad batch, periodic jumps at shards or
schedule boundaries, smooth-loss-poor-samples at tokenizer or evaluation
mismatch — and the injected-failure run executes it: a too-high learning
rate spikes both curves with its gradient-norm trace departing two steps
before the loss does, a corrupted batch moves both curves together and back,
a bf16 master weight flattens both while the gradient norm stays alive
(0.050, ruling out a dead loop), and a softmax that overflows goes
non-finite at a specific step. Each row names a different owner, and the
fix for a label-shift bug and the fix for an overfit model have nothing in
common.

The second fix is the precision contract, and its trade is memory for
numerical safety. BF16 keeps FP32's exponent range, so it needs none of
FP16's loss-scaling machinery — that is why this run trains in it — but it
gives up mantissa bits, and the loss lands in a specific place: an optimizer
update is usually a small correction added to a much larger accumulated
value, and below some ratio the correction rounds away entirely against the
accumulator. The update does not error; it simply does not happen. The
contract is therefore mixed — bf16 for activations and matrix multiplies,
fp32 for accumulation, optimizer state, and the authoritative weight
update, plus explicit non-finite checks (Micikevicius et al., 2018) — and
the trade is measured both ways: the planted bf16-master learner flatlines
at 2.418 while the fp32-master control descends to 2.358, and the overflow
run goes non-finite at step 3, where a check stops the run with step
attribution and its absence completes with a wall of inf then NaN and
neither. The third fix is the continued-pretraining discipline (begin near
the base run's final learning rate, mix general replay data, evaluate
domain gain and general regression in the same report, version the new
mixture separately — Gururangan et al., 2020), whose trade is that a
continued run gaining the target domain while silently losing the baseline
has not improved the model; it has traded one capability for another
without saying so.

## Who owns the loop

- **The data team** owns the epoch effect: a validation rise as the model
  approaches one full epoch (0.95 at the end here) is a data-ownership
  signal, and the as-of split contract is theirs.
- **The training team** owns the schedule and the precision contract: the
  cosine floor, the learning-rate bump, and the mixed bf16/fp32 rule with
  its non-finite checks decide whether an update lands at all.
- **The evaluation team** owns the measurement row: each validation point
  samples the held-out set rather than consuming it, and ruling out the
  sampling explanation takes paired runs across seeds — the ablation
  harness's job.
- **The ML-infra team** owns the telemetry: the gradient-norm trace that
  departs two steps before the loss does, and the non-finite check that
  attributes the first bad step, are the instrumentation that turns a
  symptom into an owned subsystem.

## Check your mental model

1. Both training and held-out loss are flat after 2,000 steps. Why does that
   rule out overfitting specifically?

<details>
<summary>Answer</summary>

Because overfitting requires the model to be learning *something* — its
signature is training loss falling while held-out loss stalls or rises. If
training loss is flat too, the model has not fit the training distribution
either, so there is nothing yet to over-fit. Flat-and-flat points at the loop:
a label shift that makes the target unpredictable, a mask that hides the
context, an optimizer that is not stepping, or a learning rate small enough to
do nothing. That is a different owner and a different fix.

</details>

2. BF16 does not overflow the way FP16 does. Why does it still need FP32
   optimizer state?

<details>
<summary>Answer</summary>

Overflow and precision are separate failures. BF16 keeps FP32's exponent range,
so the large-magnitude problem FP16 has — gradients that exceed the representable
range and need loss scaling — does not arise. What BF16 gives up is mantissa
bits, which is a *resolution* problem: an optimizer update is typically a small
correction added to a much larger accumulated weight or moment, and below some
ratio the correction rounds away entirely against the accumulator. Keeping the
optimizer state and the authoritative update in FP32 preserves that resolution
while still letting the far larger matrix multiplies run in cheap BF16.

</details>

3. A continued pretraining run improves the target domain by 8% and the report
   stops there. What is missing, and why is it not a formality?

<details>
<summary>Answer</summary>

The general-capability measurement on the same checkpoint. Continued
pretraining changes the data distribution, so the mechanism that produces the
domain gain is the same one that can erase base capability — the two results
are not independent, and reporting only the gain describes half of a trade as
if it were a win. That is why the rule is to evaluate domain gain and general
regression together in one report, and to version the new mixture separately
so the comparison has a named baseline to be against.

</details>

## Next

Return to [the pretraining stage](../) for the reproduction commands, or
continue the mission at [stage 03 — SFT](../../03-sft/), where the objective
stops being next-token agreement with web text and starts being the answer a
person wrote.
