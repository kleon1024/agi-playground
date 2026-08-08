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

## The fix and its trade

The fix is the order of operations: calibrate each conditional first, then
chain. The executed read shows the failure the order prevents — chaining
an overconfident click head multiplies its 2.25x inflation through to a
0.27 order estimate against the independent model's correct 0.12, so the
constraint preserves the error while adding the appearance of rigor.

The trade, named: calibration is a per-head, per-slice job that must be
re-run when traffic changes, which is real ongoing work — the chain by
itself is a one-line fix that looks done. That is exactly the trap: the
constraint is a consistency guard, and treating it as a substitute for
calibration manufactures a worse estimate than doing nothing. The correct
order — calibrate, then chain — costs the calibration team's time on
every head, and the alternative costs the downstream value estimate
every time an uncalibrated head is shipped.

## Who owns the loop

- **The model team** owns each head's calibration and its per-slice check
  — the chain is applied after the heads are honest, never instead of it.
- **The serving team** owns the chained read and the order of operations
  at score time: calibration runs before the product, so a new head
  cannot enter the chain uncalibrated.
- **The evaluation team** owns the constraint-versus-independent
  comparison — the read that proves the chain is helping, not
  manufacturing a worse estimate.

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
