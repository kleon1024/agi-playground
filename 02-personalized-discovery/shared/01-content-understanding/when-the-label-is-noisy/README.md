---
status: verified
level: applied
base: scratch
label: When the label is noisy
verified: 2026-08-07
---

# The label the threshold cannot trust

**Question:** [stage 01's content classification](../) keeps items above a
confidence threshold. This chapter reads the executed noisy-label run and
asks what the threshold actually gates.

**Before this:** [stage 01 — content understanding](../) and its executed
classifier.

## The noise, executed

The run ([record](runs/2026-08-07-noise-read.md)) classifies five items
with a noisy oracle at threshold 0.70:

| item | true | label | confidence | verdict |
|---|---|---|---|---|
| a | recipe | recipe | 0.91 | kept, ok |
| b | recipe | recipe | 0.84 | kept, ok |
| c | news | recipe | 0.78 | kept, wrong |
| d | recipe | news | 0.74 | kept, wrong |
| e | news | news | 0.62 | cut, ok |

## Two readings

**The threshold gates confidence, not truth.** All four kept items cleared
0.70, but two of them carry the wrong label — the confidence is about how
sure the model is, not about whether the label is correct. Precision
falls from 100% to 50% on the kept set without the threshold changing at
all.

**Precision is a property of the label source first.** Raising the
threshold would remove some noise but also removes correctly-labeled low-
confidence items (e's label is right; it is just uncertain). The lever
that actually fixes precision is upstream — cleaning the labels or
weighting label sources — and the threshold only decides how much noise
to let through. That ordering is why stage 01's classifier is built on
the interaction log, not on a model's own confidence.

## Evidence boundary

The executed hand-built label table (illustrative, deterministic). It
demonstrates the mechanism; real label noise is per-source and
correlated, which changes the exact numbers but not the ordering.

## Check your mental model

Answer each before opening it.

**1. Why does the threshold keep the two wrong items?**

<details>
<summary>Answer</summary>

Because confidence measures the model's certainty, and the model can be
confident about a wrong label — it was trained on the same noisy source
that produced the label. Item c is confidently labeled recipe because the
training data said so. The threshold separates certain from uncertain; it
cannot separate correct from incorrect.

</details>

**2. What would fix the kept-set precision?**

<details>
<summary>Answer</summary>

Cleaning the label source — resolving c and d against a trusted signal —
before classification, so the model learns from truth. Raising the
threshold only narrows the window; it does not change what is inside it.
The executed run makes the trade visible: e is cut despite being right,
the price of using confidence as the only gate.

</details>

## Next

Back to [stage 01](../), or to
[the threshold that rescues the tail](../when-the-threshold-rescues-the-tail/)
for the head-versus-tail side of the same gate.
