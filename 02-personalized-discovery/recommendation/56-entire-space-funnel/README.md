---
status: verified
level: applied
base: scratch
label: Entire-space funnel
verified: 2026-08-07
---

# The sparse target is learned on the wrong population

**Question:** stage 04 predicted several labels off one shared trunk and
left each head to its own training set. This stage asks what happens when
the rarest label — payment — is only observed below a click, and answers:
a head trained on the clicked subset is both starved and
selection-biased, so the fix is to model the funnel on the full exposure
space and derive the conditional instead of training it directly.

**Before this:** [stage 04 — fine-rank](../../shared/04-fine-rank/) for the
multi-task trunk this stage's trick plugs into, and [stage 05 — the value
tree](../../shared/05-value-tree/) for why each probability must be honest.

## The two training sets, executed

The run ([record](runs/2026-08-07-entire-space-funnel.md)) generates
impressions with a known click rate and a pay-given-click rate, then
trains a pay head on the clicked subset and an ESMM-style head on the
full space:

| head | positives | cvr auc |
|---|---:|---:|
| clicked subset | 705 | 0.735 |
| entire space (ctcvr) | 936 | 0.740 |

## The mechanism, named

Payment is a funnel event: it is only observed after a click, so a pay
head trained on clicked samples never sees the impressions that did not
click. That is not just fewer positives — it is a different statistical
problem, because the training population (clicked) differs from the
population the head must score (all exposures). The ESMM-style trick
trains two heads on the full space: a CTR head on every impression, and
a CTCVR head on every impression with the product label click-and-pay.
The pay conditional is then derived as CTCVR over CTR, which keeps the
funnel constraint p(pay) <= p(click) structural and gives the sparse
event the whole exposure space as its ground.

## Why this belongs in the mission

The mission's funnel is what makes the three systems one: every stage
that follows — the value tree, the ads auction, the budget pacing —
multiplies probabilities together. A conditional trained on the wrong
population is biased even when its ranking looks fine, and the bias
propagates into every product of probabilities downstream. This stage is
where the funnel stops being a diagram and becomes the training scheme.

## Evidence boundary

The executed synthetic read over declared click and pay rates
(illustrative, deterministic). It demonstrates the population and
positives effect; real entire-space modeling needs the joint label
distribution, the funnel's intermediate events, and a check that the
derived conditional stays calibrated in the slice where CTR is small.

## Check your mental model

Answer each before opening it.

**1. Why is training the pay head on clicked samples more than just
fewer positives?**

<details>
<summary>Answer</summary>

Because the training population is different from the scoring
population: clicked impressions are a selected subset, so the head
learns pay inside that subset and never sees the exposures where pay is
structurally impossible. Fewer positives is the symptom; the selection
bias is the disease, and it is why the fix is a different training
scheme, not a bigger loss weight.

</details>

**2. What does the multiplicative CTCVR structure guarantee?**

<details>
<summary>Answer</summary>

That p(pay) is never larger than p(click), because it is the product of
the click probability and a conditional bounded by one. Probability
semantics are enforced by construction instead of by post-hoc clamping,
which is the consistency this mission's downstream stages rely on when
they multiply scores together.

</details>

## Next

The funnel's labels also arrive late: [a conversion that happens
tomorrow is labeled a negative today](when-the-cvr-is-censored/) — the
executed read: censored pay ranking collapses to 0.448 versus 0.618 for
the full-space head.

Deriving pay as a ratio has its own failure: [the ratio explodes
wherever p(click) is tiny](when-the-ctcvr-disagrees/) — the executed
read: at 2% CTR a small CTCVR error is a 3x swing in the derived
conditional.
