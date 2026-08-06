---
status: verified
level: applied
base: scratch
label: The split shift at the scarcest
verified: 2026-08-06
---

# The scarcest endpoint carries the largest split shift

**Question:** [stage 03's second endpoint](../) ran the comparison on
NR-PPAR-gamma, the most imbalanced Tox21 endpoint. This chapter reads the
recorded split and asks what the shift adds to the verdict.

**Before this:** [stage 03's second endpoint](../) and its recorded split.

## The shift, read

The run ([record](runs/2026-08-06-split-shift.md)) reads the recorded
split:

| number | value |
|---|---|
| n_train / n_test | 5,154 / 1,289 |
| scaffold overlap | 0 |
| train positive rate | 2.29% |
| test positive rate | 5.28% (2.3x) |

## Two readings

**Whole-scaffold assignment moves a larger fraction of a scarce minority
class.** With only 118 train positives, assigning whole scaffold groups to
train or test moves proportionally more of the minority class than it
would at SR-MMP's 689 — the test set ends up 2.3x more positive than
train. The split is still leak-free (overlap 0), but the label balance
shifts, and the shift is a real property of scaffold splitting on a rare
class.

**The shift is the same confound the inconclusive verdict measures.** The
model's wide seed spread (0.0620) on this endpoint and the 2.3x positive
shift are the same phenomenon: scarcity amplifies whatever moves the
minority class. The split shift is the data-side expression; the
inconclusive verdict is the model-side expression. Reading both is what
connects the no-result to its cause.

## Evidence boundary

The recorded split summary (one endpoint, one scaffold split, one seed).
It reads that artifact; it does not re-split.

## Check your mental model

Answer each before opening it.

**1. Why does the shift not violate the scaffold guarantee?**

<details>
<summary>Answer</summary>

Because overlap and balance are different properties. The scaffold split
guarantees no scaffold crosses train/test (overlap 0), which is the
leakage guarantee. It does not guarantee the label distribution is
preserved — scaffold groups cluster by activity, so moving groups can
shift the positive rate. The 2.3x shift is a balance property, not a
leakage violation.

</details>

**2. What does the shift add to the inconclusive verdict?**

<details>
<summary>Answer</summary>

It explains why the model's variance is so large. A 2.3x positive shift
means the model trains on a nearly-empty minority class and evaluates on
a denser one — a harder task with more seed sensitivity. The shift is the
data-side cause of the 0.0620 spread, which is the model-side reason the
verdict is inconclusive. The two numbers are one story.

</details>

## Next

Back to [stage 03](../), or to
[the no-result that is a real result](../when-the-verdict-is-inconclusive/)
which reads the same stage's verdict side.
