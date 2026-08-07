---
status: verified
level: applied
base: scratch
label: When the noise is too high
verified: 2026-08-07
---

# The noise is too high and the order collapses

**Question:** [stage 40's privacy-safe attribution](../) adds noise to
channel counts. This chapter reads the executed epsilon sweep and asks
where the privacy dial breaks the budget decision.

**Before this:** [stage 40 — privacy-safe attribution](../) and its
executed DP-noise model.

## The collapse, executed

The run ([record](runs/2026-08-07-noise-is-too-high-read.md)) sweeps
epsilon with one fixed draw per level:

| epsilon | noisy counts | rank | order preserved |
|---|---|---|---|
| 5.0 | 485, 308, 263 | search, display, email | True |
| 2.0 | 470, 330, 265 | search, display, email | True |
| 0.5 | 450, 230, 350 | search, email, display | False |

## The reading

At epsilon 5 the order survives; at 0.5 it collapses — the same unlucky
draw that leaves the order intact at 5.0 breaks it when the noise scale
is four times larger. The privacy guarantee and the decision accuracy
are the same dial: lowering epsilon strengthens privacy and weakens the
signal the budget follows. Epsilon has to be chosen so the noisiest
plausible draw still keeps the budget decision intact — the collapse
point is a design constraint, not an accident.

## Evidence boundary

The executed sweep over three declared epsilon levels with a fixed draw
(illustrative, deterministic, assumed Laplace noise). It demonstrates
the mechanism; real privacy-safe attribution needs the true epsilon
budget and a measured decision-error rate over many draws.

## Check your mental model

Answer each before opening it.

**1. Why does the same draw break the order at low epsilon?**

<details>
<summary>Answer</summary>

Because the noise scale is 1 over epsilon. At epsilon 5 the noise is
small — the draw nudges counts but the gaps survive. At epsilon 0.5 the
same draw is four times larger: display falls 80 while email rises 90,
and the 50-count gap between them flips. Lower privacy noise is not a
smaller version of the problem; it is a different problem where order
becomes random.

</details>

**2. What does "the noisiest plausible draw still keeps the decision
intact" require?**

<details>
<summary>Answer</summary>

That epsilon is set against the worst case, not the average. The budget
decision is ordinal, so the design must survive the draw that pushes
each channel hardest — if that draw can flip display and email, the
budget moves on noise. Epsilon has to be large enough that even the
unlucky draw preserves the rank the budget follows, which is the
collapse-point constraint the sweep exposes.

</details>

## Next

Back to [stage 40](../). The
[budget-split detour](../when-the-budget-splits/) shows the second
pressure on epsilon: the same privacy budget split across many reports.
