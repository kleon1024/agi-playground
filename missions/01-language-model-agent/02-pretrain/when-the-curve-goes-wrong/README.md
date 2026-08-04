---
status: draft
level: applied
base: none
label: When the curve goes wrong
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

The value of the table is that each row names a *different owner*. Do not go
from a bad sample straight to a bigger model — identify which subsystem the
evidence belongs to first, because the fix for a label-shift bug and the fix
for an overfit model have nothing in common.

The 3.0689-to-3.0984 rise above is row three read carefully: both losses fell,
then one turned. Its three candidate owners are the data (approaching one full
epoch), the schedule (a cosine floor too high to settle into), and the
measurement itself (each point samples the held-out set rather than consuming
it). Ruling any of them out takes paired runs across seeds, which is what
[the ablation harness](../../../../platform/data/01-ablation-harness/) is for.

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
this mission's evidence.

Primary references: Micikevicius et al., *Mixed Precision Training* (2018) for
the FP32 master-weight contract; Gururangan et al., *Don't Stop Pretraining*
(2020) for continued-pretraining evaluation; Peng et al., *YaRN* (2023) for
context extension.

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
