---
status: verified
level: applied
base: scratch
label: Where the decoder looks
verified: 2026-08-06
---

# Where does the decoder look when the image matters?

**Question:** the recorded accuracy shows the vision pathway separates from
text-only exactly where the question cannot leak — color questions, 50.1%
versus 27.2%. The naive mechanism is "the decoder attends to the image when
it needs it." This chapter measures that claim, and the measurement
contradicts it.

**Before this:** [stage 01's vision fusion](../) and its recorded accuracy.

## The measurement

The run retrains the vision pathway (seed 0, the stage's own recipe) and, for
every held-out example, captures the last fusion layer's attention weights
via the diagnostic method that never touches the training path. It then
splits the examples by question type and averages how much of each text
query's attention lands on the 64 vision-prefix tokens
([run record](runs/2026-08-06-vision-attention-mass.md)):

| question type | n | mean vision attention mass |
|---|---:|---:|
| color (leak-proof) | 261 | 0.01029 |
| other | 523 | 0.01226 |

The hypothesis fails: the decoder spends **less** mean attention mass on the
vision prefix for color questions — 0.84x, not more. And the absolute mass
is tiny: about one percent of a text query's weight lands on 64 vision
tokens at this layer. If the vision pathway's separation on color questions
is real (the recorded accuracy says it is), attention mass at layer 3 is not
the carrier.

## Attention mass is not the explanation

This is the attention-is-not-explanation result (Jain & Wallace, 2019),
measured on this repo's own model instead of quoted. Attention weights are a
distribution; what the decoder actually uses is the *content* the value
vectors contribute. A prefix can receive one percent of the weight and
carry the answer, or receive half the weight and carry nothing — the mass
does not tell you which. Two plausible carriers remain, and the chapter does
not adjudicate between them: the vision value vectors' content at this
layer, or the vision prefix being read at earlier layers where the separation
starts.

That the separation exists is the mission's recorded finding; this chapter
adds what it is not — a weight-magnitude effect. The practical lesson for
the learner: don't debug a multimodal model with attention heatmaps alone.
The heatmap shows where the model *could* look; whether it *used* what it
saw is a question about values and accuracy, which is why the mission's
text-only baseline exists as the control.

## The fix and its trade

The fix is the accuracy control, not the heatmap: the text-only baseline is
the diagnostic that tells you whether the model used the image, because a
one-percent attention mass can carry the answer and a fifty-percent mass
can carry nothing. The trade is that the fix costs an easy visualization —
the naive "the decoder attends to the image when it needs it" story is
false here (0.84x mass on the leak-proof color questions, about one percent
absolute), and what replaces it is harder: the value vectors' content at
this layer, or the prefix being read at earlier layers, are the two
remaining candidates and this chapter does not adjudicate between them.
The claim is scoped deliberately: attention is not the explanation *here*,
which is the position Jain and Wallace (2019) argued for and Wiegreffe and
Pinter (2019) qualified — attention can be explanatory under some
conditions, so a diagnostic that only reads weights cannot tell you which
case you are in.

## Who owns the loop

- **The evaluation owner** owns the diagnostic choice: the accuracy
  control and the held-out split are the evidence for whether the pathway
  used the pixels; a heatmap is a hypothesis generator, not a verdict.
- **The model team** owns the mechanism question the chapter leaves open —
  where the separation actually lives (values at this layer, earlier
  layers, or both) — and is the owner who would run the probing that
  answers it.
- **The report owner** owns the separation claim itself, backed by the
  recorded accuracy (50.1% vs 27.2% on color) and the text-only control,
  so the weight story and the accuracy story are never confused in the
  mission's verdict.

## Evidence boundary

Layer 3 (the last of four), one seed, the stage's greedy eval forward; the
accuracy numbers are the recorded 3-seed means, not re-measured here. It
shows attention mass does not explain the separation on this model at this
layer; it does not identify where the separation does live, does not cover
the other layers, and does not claim attention is never diagnostic — it is
not the explanation *here*.

## Check your mental model

Answer each before opening it.

**1. Why can a one-percent attention mass still carry the answer?**

<details>
<summary>Answer</summary>

Because attention weights decide *how much* of each value vector is mixed
in, not *what* the value vectors contain. A single vision token whose value
encodes the disambiguating feature can determine the output even when its
weight is small, if the competing text values are neutral. Mass is a budget;
the information is in the content it buys.

</details>

**2. The accuracy separates on color questions, the attention mass does not.
What does that combination rule out?**

<details>
<summary>Answer</summary>

It rules out "the model attends more to the image for color questions" as
the mechanism — the measured ratio is 0.84x, the opposite direction. It
leaves the mechanism open (value content, earlier layers, or both), which is
exactly why a diagnostic that only looks at weights would have been
misleading: the weight story and the accuracy story disagree, and the
accuracy story is the one backed by the held-out control.

</details>

## Next

Back to [stage 01's fusion](../), or forward to
[stage 06's warmup stability](../../06-warmup-stability/) where the seed-2
collapse is the next thing the vision pathway's variance exposes.
