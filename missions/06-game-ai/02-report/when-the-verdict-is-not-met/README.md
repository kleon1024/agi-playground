---
status: verified
level: applied
base: scratch
label: When the verdict is NOT MET
verified: 2026-08-06
---

# The honest NOT MET: how the verdict is built

**Question:** [mission 06's report](../) judged GRPO against both baselines
and returned NOT MET. A verdict like that is only as good as its evidence
structure: this chapter recomputes the margins from the committed JSONs and
reads the failure catalogue that explains the verdict.

**Before this:** [mission 06's outcome report](../) and its recorded
verdict.

## The margins, recomputed

The run ([record](runs/2026-08-06-not-met-recomputed.md)) reads the
committed baselines and seed JSONs:

| comparison | margin | policy's spread | verdict |
|---|---:|---:|---|
| greedy decode vs random | -0.149 | 0.016 | decisively loses |
| sampled decode vs random | -0.043 | 0.066 | within noise |
| greedy decode vs greedy baseline | -0.751 | 0.016 | decisively loses |
| sampled decode vs greedy baseline | -0.645 | 0.066 | decisively loses |

## Two readings

**The verdict is judged against the policy's own noise, not the baseline's.**
A margin is a result only when it exceeds the policy's run-to-run spread
— the mission's rule, applied per comparison. Greedy decode loses to both
baselines beyond its 0.016 spread; sampled decode is inside its 0.066 band
against random (no result) but decisively loses to the greedy baseline.
The recomputation reproduces the recorded verdict exactly.

**The catalogue is what makes NOT MET informative.** The margins say the
policy lost; the failure catalogue says why: board-independent collapse
(3/3 seeds emit one fixed action string on every held-out board), and
non-stabilizing training-time success (3/3, peaks falling back by the final
window). A policy whose greedy decode ignores the prompt cannot be saved by
any margin — the verdict is NOT MET because the mechanism is broken, and
the report shows that rather than leaving it at a number.

## Evidence boundary

The committed baselines and GRPO JSONs, three seeds each; the failure
catalogue is the recorded report's, cited. It recomputes the margins and
reads the catalogue; it does not re-train and does not re-derive the
baselines.

## Check your mental model

Answer each before opening it.

**1. Sampled decode is within noise of the random baseline yet the verdict
is still NOT MET. Why doesn't that row save it?**

<details>
<summary>Answer</summary>

Because a within-noise row is a non-result, not a win — the policy's
sampled success could be seed noise, so it cannot be claimed as beating the
baseline. And the other rows decide the verdict: greedy decode loses
decisively to both baselines, and the failure catalogue shows the greedy
path ignores the prompt entirely. NOT MET is the conjunction: no margin
clears the bar, and the mechanism is broken.

</details>

**2. Why does the report separate the margins from the failure catalogue?**

<details>
<summary>Answer</summary>

Because they answer different questions. The margins answer "did the policy
beat what it had to beat" — no. The catalogue answers "why not" — the
greedy decode collapses to a fixed action string, ignoring the board. A
verdict with only the margins would be a loss without a diagnosis; with
only the catalogue it would be a story without a score. The report's
structure keeps the number and the mechanism separate so the next stage
knows which failure to attack.

</details>

## Next

Back to [mission 06's report](../), or to
[stage 03's collapse sweep](../../03-fixing-collapse/) where the greedy
decode failure this verdict names is the thing the fixes targeted.
