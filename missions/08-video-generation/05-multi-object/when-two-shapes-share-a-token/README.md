---
status: verified
level: applied
base: scratch
label: When two shapes share a token
verified: 2026-08-06
---

# One token per frame, two objects: where the capacity limit shows

**Question:** [stage 05](../) composites two independently-moving shapes
into one scene while the codec still emits one 64-entry token per frame.
This chapter reads the recorded JSONs and asks what the second object costs
when one token must represent both positions.

**Before this:** [stage 05's multi-object run](../) and stage 02's
single-object baseline.

## The axis, read

The run ([record](runs/2026-08-06-object-axis.md)) reads the recorded JSONs:

| seed | 1-object MSE | 2-object MSE | 2-object exact-match |
|---|---:|---:|---:|
| 0 | 0.0804 | 0.1429 | 0.007 |
| 1 | 0.0865 | 0.1486 | 0.027 |
| 2 | 0.0882 | 0.1533 | 0.287 |
| mean | 0.0851 | 0.1483 | — |

## Two readings

**The second object costs ~74% more reconstruction error.** One token per
frame has to carry both objects' positions, and the limit shows in the
number: 0.0851 -> 0.1483 mean MSE, with exact-match collapsing to
0.7%-28.7%. The codec's capacity — not compute, not the sequence model —
is the binding constraint along this axis, the same pattern stage 04 found
along the frame-count axis.

**The stage still closes MET, and the capacity read is why.** 2-object mean
0.1483 beats the frame-repeat baseline 0.2193 by a margin 6.8x the 0.0104
seed spread, and sits within 2.3% of the oracle (true-token) ceiling. The
verdict is a finding, not a failure: the tokenizer is what is missing, and
the mission says so instead of re-scaling the number into a fake win.

## Evidence boundary

The committed stage-02 (1-object) and stage-05 (2-object) seed JSONs, three
seeds each, 8 frames; it reads those artifacts and does not re-train. The
occlusion claim and the seed-2 wall-clock variance are the stage's recorded
results, not re-measured here.

## Check your mental model

Answer each before opening it.

**1. Two objects still clear the baseline. Why does the chapter call the
result a capacity limit rather than a pass?**

<details>
<summary>Answer</summary>

Because the mission's question is about the system's shape, not just its
verdict. The margin clears the bar — MET — but the 74% MSE jump and the
exact-match collapse identify the mechanism: one token per frame cannot
carry two objects' positions. The pass is real and the limit is real, and
reporting both is what keeps the verdict honest.

</details>

**2. Why does exact-match fall so much harder than MSE when the second
object arrives?**

<details>
<summary>Answer</summary>

Because exact-match is all-or-nothing at the token level. When one token
must represent two positions, the codec has to compromise on both, and any
compromise changes which codebook entry is nearest — so the token sequence
diverges even when the rendered frames stay close in pixel space. MSE
measures the compromise; exact-match measures the discretization failure,
which is the sharper signal of a capacity problem.

</details>

## Next

Back to [stage 05](../), or to
[stage 06 — longer and multi-object](../../06-longer-and-multi-object/) which
runs both axes together to complete the grid.
