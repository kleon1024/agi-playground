---
status: verified
level: applied
base: scratch
label: When the constraint hurts
verified: 2026-08-07
---

# The chain inherits the click error

**Question:** [stage 62](../) chains the funnel for consistency. This
chapter asks whether enforcing the constraint can ever hurt, and answers:
yes — the chain is only as honest as its inputs, so enforcing monotonicity
on an uncalibrated click head manufactures a worse order estimate.

**Before this:** [stage 62 — funnel consistency](../).

## The chain vs the independent model, executed

The run ([record](runs/2026-08-07-constraint-hurts.md)) compares an
independent order model with a chained read over a bad and a calibrated
click head:

| model | p(order) |
|---|---:|
| independent order model | 0.12 (calibrated) |
| chained, bad click model | 0.27 (2.25x too high) |
| chained, calibrated click model | 0.12 (correct) |

## The reading

Enforcing the funnel on top of an overconfident click head manufactures a
worse order estimate than the independent one: the chain faithfully
multiplies the click head's inflation through to the order probability.
The ordering is a good constraint, but it is applied after calibration,
not instead of it — the two fixes are the same fix: make each conditional
honest first.

## Evidence boundary

The executed read over declared head outputs (illustrative, deterministic).
It demonstrates the propagation; real systems must calibrate each
conditional before chaining and treat the constraint as a consistency
guard, not a substitute for calibration.

## Check your mental model

Answer each before opening it.

**1. Why does chaining an uncalibrated head make things worse?**

<details>
<summary>Answer</summary>

Because the chain is a product of conditionals. A click head that
overstates its probability by 2.25x passes that inflation straight into
the order estimate — the constraint preserves the error while adding the
appearance of rigor.

</details>

**2. What is the correct order of operations?**

<details>
<summary>Answer</summary>

Calibrate each conditional, then chain. The constraint enforces that the
composed probabilities are monotone; calibration enforces that they are
honest — one does not replace the other.

</details>

## Next

Back to [stage 62](../). The raw symptom the chain exists to fix: [heads
that contradict the funnel on the page](../when-the-order-exceeds-the-click/).
