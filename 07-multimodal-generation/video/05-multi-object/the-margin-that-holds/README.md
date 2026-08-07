---
status: verified
level: applied
base: scratch
label: The margin that holds
verified: 2026-08-06
---

# Two objects, one token per frame, and the margin still clears

**Question:** [stage 05's multi-object run](../) composited two shapes
while the codec emits one token per frame. This chapter reads the recorded
JSONs and asks whether the verdict survived the capacity stress.

**Before this:** [stage 05's multi-object run](../) and its recorded JSONs.

## The margin, read

The run ([record](runs/2026-08-06-multi-margin.md)) reads the recorded
numbers:

| | value |
|---|---|
| 2-object mean MSE | 0.1483 |
| seed spread | 0.0104 |
| frame-repeat baseline | 0.2193 |
| margin | 0.0710 (6.8x the spread) |

## Two readings

**The verdict holds: two objects still beat frame-repeat by ~6.8x the seed
spread.** The capacity question — can one per-frame token carry two
objects' positions — is real, and the cost shows in the MSE jump (0.0851
single-object -> 0.1483 two-object). But the margin clears the baseline
beyond seed noise, so stage 05 closes MET on every seed.

**The capacity limit is the finding, not a failure.** The MSE jump and the
exact-match collapse (0.7-28.7%) identify the mechanism: one 64-entry
token cannot carry both objects' state precisely. The mission reports the
limit instead of rescaling the number into a fake win — the tokenizer is
what is missing, and stage 06's combined-axis run confirms it is the
binding constraint.

## Evidence boundary

The recorded stage-05 JSONs (three seeds, 8 frames, one recipe). It reads
those artifacts; it does not re-train.

## Check your mental model

Answer each before opening it.

**1. Why is the margin-vs-spread check the right way to read a capacity
question?**

<details>
<summary>Answer</summary>

Because it separates "the mechanism degraded" from "the mechanism failed."
The MSE jump (0.0851 -> 0.1483) shows degradation; the margin clearing
the spread (0.0710 vs 0.0104) shows the generation still works beyond
noise. Both are true — capacity is stressed but the verdict holds — and
the two numbers together are what make the reading precise.

</details>

**2. What does exact-match's collapse add that MSE hides?**

<details>
<summary>Answer</summary>

It exposes the discretization failure. MSE measures the compromise in
pixel space; exact-match measures whether the token sequence still
matches the true one. When one token must represent two positions, the
nearest codebook entry shifts and the tokens diverge (0.7-28.7%) even
though the pixels stay close — the sharper signal of a capacity limit,
and why the report reads both metrics.

</details>

## Next

Back to [stage 05](../), or to
[one token per frame, two objects: where the capacity limit shows](../when-two-shapes-share-a-token/)
which reads the same runs' axis story.
