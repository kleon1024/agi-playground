---
status: verified
level: applied
base: scratch
label: When the CVR is censored
verified: 2026-08-07
---

# The head that never sees a non-click

**Question:** [stage 56](../) argues the pay head should train on the full
exposure space. This chapter makes the failure concrete: a pay head trained
only on clicked impressions ranks worse than random on the full funnel.

**Before this:** [stage 56 — entire-space funnel](../) and its executed
clicked-vs-full-space read.

## The censoring, executed

The run ([record](runs/2026-08-07-cvr-censored.md)) trains the same pay
signal on the clicked subset and on every impression:

| head | pay AUC | positives |
|---|---:|---:|
| censored (clicked subset) | 0.448 | 232 |
| full-space | 0.618 | 232 |

## The reading

The two heads see the same 232 positives; the difference is the ground they
are learned on. The censored head is trained only on impressions that
clicked, so inside that selected population pay ranking is a coin flip — and
when it scores the full funnel, it is worse than random. The full-space head
learns the same conditional on every impression and ranks correctly.
Censoring is what ESMM removes by modeling the whole exposure space; this
number is the price of not doing it.

## Evidence boundary

The executed synthetic read over declared click and pay rates
(illustrative, deterministic). It isolates the censoring effect; real
systems must also account for which exposures were even eligible and for
the position the impression was collected in.

## Check your mental model

Answer each before opening it.

**1. Why is the censored head worse than random on the full funnel?**

<details>
<summary>Answer</summary>

Because it never saw a non-click. Its only training ground is the clicked
population, where pay is conditionally rare and the ranking signal is
noise; when it scores impressions where pay is structurally impossible, it
has no information to separate them.

</details>

**2. What does "same 232 positives" prove?**

<details>
<summary>Answer</summary>

That the difference is not label scarcity — both heads see every positive.
The defect is the population the negatives are drawn from, which is the
selection-bias argument: the fix is a different training scheme, not more
data.

</details>

## Next

Back to [stage 56](../). The other face of the ratio trick: [the derived
conditional explodes wherever CTR is tiny](../when-the-ctcvr-disagrees/).
