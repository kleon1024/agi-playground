---
status: verified
level: applied
base: scratch
label: The calibration that decides
verified: 2026-08-06
---

# Why ECE is a gate, not a polish step

**Question:** [stage 04's fine-rank](../) predicts click, completion,
satisfaction, and dwell. This chapter reads the recorded run and asks what
calibration actually buys downstream.

**Before this:** [stage 04's fine-rank](../) and its recorded run.

## The numbers, read

The run ([record](runs/2026-08-06-calibration-read.md)) reads the recorded
panels:

| trunk | task recovery (naive -> balanced) | ECE before -> after Platt |
|---|---:|---:|
| hidden=8, epochs=25 | dwell 0.658 -> 0.803 | 0.0722 -> 0.0552 |
| hidden=16, epochs=60 | dwell -0.080 -> 0.809 | 0.0956 -> 0.0555 |

## Two readings

**Balanced weighting is the negative-transfer fix.** In both trunks, the
naive equal-weighting of four tasks hurts dwell — the widest trunk turns it
negative (-0.080) — and scale-normalized weighting recovers it (0.803-
0.809). The recorded recovery is the mechanism behind the stage's "shared
model" trade: the trunk helps when tasks are balanced and hurts when one
dominates the loss scale.

**Calibration is the gate the value tree depends on.** Stage 05 does
arithmetic on these probabilities, and ECE before Platt (0.0722-0.0956)
would propagate into every downstream combination. Platt scaling cuts it
~25-40%, which is what makes the numbers "what they claim to be" — the
precondition the next stage's arithmetic needs. The ECE rows are why
calibration is a gate, not a polish step.

## The fix and its trade

The fix is to treat calibration as a gate before downstream arithmetic, and
to calibrate on a set the calibrator never saw. The executed panels price
the fix: Platt scaling drops the click head's ECE from 0.0722 to 0.0552 on
the default trunk and from 0.0956 to 0.0555 on the wide trunk — the two
trunks converge to the same post-calibration ECE, which is exactly what a
calibrator is supposed to do. The isotonic lane fitting the same held-out
set to ECE 0.0000 is the trap: a calibrator with enough capacity memorizes
the validation set, so a 0.0000 ECE is evidence of leakage, not of quality.

The trade, named: calibration buys downstream arithmetic at the price of
ranking headroom and a held-out set. A monotone recalibration (Platt) can
only bend probabilities, never reorder the rank, so it is safe for the
ranker and necessary for stage 05's value arithmetic — but every calibrated
number must be re-checked when the training distribution moves, because the
calibrator and the model decay on different schedules. The ECE gate is
where the "0.3 is supposed to mean 0.3" contract is enforced before any
product-facing number is built from it.

## Who owns the loop

- **The model team** owns the calibration gate — Platt on a held-out set is
  the shipping bar, and the isotonic-overfit trap is theirs to catch.
- **The value-tree team (stage 05)** owns the consumption contract: they
  receive calibrated probabilities and must re-check ECE when the value
  arithmetic changes.
- **The evaluation team** owns the ECE measurement on a set that did not fit
  the calibrator, and the re-check when either the model or the calibrator
  is retrained.

## Evidence boundary

The recorded fine-rank run (synthetic interactions, two trunk sizes, click
head calibration on 400 held-out examples). It reads those artifacts; it
does not re-train and the ECE values characterize the synthetic task set.

## Check your mental model

Answer each before opening it.

**1. Why does the wider trunk make dwell negative under naive weighting?**

<details>
<summary>Answer</summary>

Because naive weighting lets the loss scale of each task decide its
importance. In the wider trunk, click and completion dominate the gradient,
and dwell — a regression with a different magnitude — gets squeezed until
it correlates negatively. Scale-normalized weighting removes the magnitude
confound, which is why the same trunk recovers to 0.809.

</details>

**2. What breaks downstream if ECE is left at 0.09?**

<details>
<summary>Answer</summary>

The value tree's arithmetic. Stage 05 combines these probabilities and
weighs them; a click prediction that is 9 points off in expectation means
every combination built from it is wrong by that amount. The calibration
break detour shows the consequence: the same strategy, different
calibration, different slate. ECE is the gate that keeps the downstream
arithmetic honest.

</details>

## Next

Back to [stage 04](../), or to
[when the shared model hurts](../when-sharing-hurts/) which reads the
negative-transfer half of the same run.
