---
status: verified
level: applied
base: scratch
label: When the verdict is inconclusive
verified: 2026-08-06
---

# The no-result that is a real result

**Question:** [stage 03](../) ran the SR-MMP comparison on a second,
deliberately more imbalanced endpoint (NR-PPAR-gamma, 2.9% positive) and
returned INCONCLUSIVE. This chapter reads the recorded seeds and shows what
"the gap sits inside the spread" actually means.

**Before this:** [stage 03's second-endpoint run](../).

## The verdict, read

The run ([record](runs/2026-08-06-inconclusive-read.md)) reads the recorded
seeds:

| arm | mean ROC-AUC | seed spread |
|---|---:|---:|
| descriptor baseline | 0.6554 | 0.0044 |
| trained model | 0.6591 | 0.0620 |
| gap (model - descriptor) | +0.0037 | vs larger spread 0.0620 |

## Two readings

**A nominal lead that is not a win.** The trained model's mean is 0.0037
above the descriptor baseline — but that is roughly 1/17th of its own
0.0620 seed spread. By the rule `mission.yaml` declared before any code ("if
the gap is smaller than the run-to-run spread, the honest answer is 'no
result'"), this is INCONCLUSIVE, the same bar stage 02 used to reach a clean
NOT MET on SR-MMP.

**Scarcity is the measurable cause, not a guess.** NR-PPAR-gamma's training
split has 118 positive compounds versus SR-MMP's 689 — roughly 6x fewer —
and the model's spread scales with that scarcity (0.0620 here vs 0.0159 on
SR-MMP) while the convex descriptor baseline's barely moves (0.0044 vs
0.0010). The no-result is the variance showing up, and the variance is the
scarcity showing up.

## Evidence boundary

The six committed seed JSONs (one endpoint, three seeds per arm, one
architecture, one scaffold split); it reads those artifacts and does not
re-train. It does not claim the pattern holds at a third endpoint — that is
stage 04's job — and says nothing about drug efficacy, per `mission.yaml`'s
`does_not_prove`.

## Check your mental model

Answer each before opening it.

**1. The model's mean is higher. Why does the chapter refuse to call it a
win?**

<details>
<summary>Answer</summary>

Because the mission's bar is margin beyond run-to-run spread, and the gap
(0.0037) is a fraction of the model's own spread (0.0620). A different
random seed could plausibly flip the sign — that is what "inside the
spread" means. Calling it a win would be the exact failure the declared
bar exists to prevent.

</details>

**2. Why is INCONCLUSIVE a legitimate mission outcome rather than a
failure to run the experiment?**

<details>
<summary>Answer</summary>

Because the mission's decision framing allows three outcomes — replicates,
reverses, or inconclusive — and the experiment ran exactly as designed.
The no-result is informative: it says scarcity inflates model variance so
much that neither arm can be separated on this endpoint, which is a real
property of the data, not a missing measurement.

</details>

## Next

Back to [stage 03](../), or to
[stage 04's mid-range point](../../04-third-endpoint/) which adds the third
endpoint and tests whether the scarcity-variance pattern holds.
