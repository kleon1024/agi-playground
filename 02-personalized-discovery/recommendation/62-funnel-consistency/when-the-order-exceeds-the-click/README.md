---
status: verified
level: applied
base: scratch
label: When the order exceeds the click
verified: 2026-08-07
---

# The impossible probability, on the page

**Question:** [stage 62](../) fixes the conditional-as-marginal read. This
chapter shows the raw symptom the pipeline emits before the fix: heads
trained on different labels producing order probabilities above click
probabilities.

**Before this:** [stage 62 — funnel consistency](../).

## The three heads, executed

The run ([record](runs/2026-08-07-order-exceeds-click.md)) reads three
head outputs:

| sample | p(click) | p(order) | p(pay) | contradiction |
|---|---:|---:|---:|---|
| strong-intent item | 0.12 | 0.15 | 0.31 | order > click |
| cold lead | 0.02 | 0.04 | 0.07 | order > click |
| normal item | 0.30 | 0.08 | 0.02 | ok |

## The reading

These heads were trained on different labels and nothing ties them
together, so their outputs can violate the funnel. The next stage
multiplies these numbers into a value estimate, and a p(order) above
p(click) is not a model nuance — it is a probability that cannot exist.
Monitoring the violation rate is the cheapest funnel-consistency check a
team can run, because it needs no labels: the contradiction is visible in
the outputs themselves.

## Evidence boundary

The executed read over three declared head outputs (illustrative,
deterministic). It demonstrates the symptom; real systems must monitor the
violation rate per slice on serving traffic and alert before the value
estimates are consumed.

## Check your mental model

Answer each before opening it.

**1. How can p(order) exceed p(click) if order requires click?**

<details>
<summary>Answer</summary>

Only if the two heads were trained on different populations and their
outputs are compared as if they were marginals on the same population.
Each head is individually plausible; their combination is impossible.

</details>

**2. Why is the violation rate a free check?**

<details>
<summary>Answer</summary>

Because it needs no ground truth: a contradiction is detectable in the
model outputs alone, so it can run continuously on serving traffic at
negligible cost.

</details>

## Next

Back to [stage 62](../). The constraint's own failure: [enforcing the
funnel on an uncalibrated click head manufactures a worse order
estimate](../when-the-constraint-hurts/).
