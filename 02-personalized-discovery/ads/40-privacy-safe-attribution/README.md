---
status: verified
level: applied
base: scratch
label: Privacy-safe attribution
verified: 2026-08-07
---

# Attribution that cannot see the individual

**Question:** stage 30's measurement reads per-user behavior. This stage
asks what attribution looks like when the platform must not see the
individual and answers: differential privacy — noise is added to
channel counts, and the noise trades privacy against the accuracy of
the budget decision.

**Before this:** [stage 30 — ads measurement](../30-ads-measurement/)
for what the measurement must decide, and [stage 27 — bid
strategy](../27-bid-strategy/) for the budget the attribution feeds.

## The noisy rank, executed

The run ([record](runs/2026-08-07-privacy-safe-attribution.md)) adds
Laplace noise at epsilon 2.0:

| channel | true | noisy |
|---|---:|---:|
| search | 480 | 462 |
| display | 310 | 275 |
| email | 260 | 275 |

True rank: search, display, email. Noisy rank: search, email, display.
Order preserved: no.

## The mechanism, named

Attribution needs aggregated channel counts; privacy forbids publishing
the true counts because an adversary could isolate an individual's
contribution. Adding calibrated noise hides any individual's
contribution while keeping the aggregate roughly usable. The executed
draw shows the trade: the noise flipped display and email (275 and 275),
so the rank that decides budget changed even though the true order was
clear. Epsilon is the dial between the two.

## Why this belongs in the mission

The ads track's budget decision depends on measurement, and measurement
now runs under privacy constraints that change what can be published.
This is the mission's frontier claim for ads: the numbers the budget
uses have to survive noise, and the noise-too-high detour shows the
collapse point where the decision breaks. The mission's discipline
applies — the privacy mechanism is admitted only where its error mode is
measured, and the budget-splits detour prices the shared-resource
problem.

## Evidence boundary

The executed noisy draw over three declared counts (illustrative,
deterministic, assumed Laplace noise). It demonstrates the mechanism;
real privacy-safe attribution needs the true epsilon budget, the noise
mechanism, and a measured decision-error rate over many draws.

## Check your mental model

Answer each before opening it.

**1. What does the noise protect, and what does it cost?**

<details>
<summary>Answer</summary>

It protects the individual — no single user's contribution can be
recovered from the published aggregate. The cost is decision accuracy:
the executed draw reorders display and email, so the attribution rank
the budget follows changed. Epsilon is the dial: more noise means
stronger privacy and a weaker signal for the budget decision.

</details>

**2. Why is the order of the noisy counts the thing that matters?**

<details>
<summary>Answer</summary>

Because the budget decision is ordinal — it moves spend toward the
channels that rank highest. A small error in absolute counts is
harmless; an error that flips the order moves money. The executed run
shows the flip: search stays on top, but display and email swap at 275,
so the second allocation decision is wrong even though the totals are
nearly right.

</details>

## Next

The frontier ads track continues. Next is [stage 41 — LLM creative
generation](../41-llm-creative-generation/), where the creative itself
is generated.

A detour from here: [the noise is too high and the order
collapses](when-the-noise-is-too-high/) — the executed sweep read:
at epsilon 5 the order survives, at 0.5 the noise reorders email above
display, so the noisiest plausible draw must still keep the budget
decision intact.

Another detour: [the privacy budget splits and dilutes every
report](when-the-budget-splits/) — the executed split read: one report
gets epsilon 2.0 and noise scale 0.5, 100 reports get epsilon 0.02
each and noise scale 50, so every additional report dilutes the signal
of all the others.
