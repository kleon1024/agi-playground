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
