---
status: verified
level: applied
base: scratch
label: When the frames double
verified: 2026-08-06
---

# Doubling the frames: what the same recipe says at 16

**Question:** [stage 04](../) doubled stage 02's clip length from 8 to 16
frames with everything else unchanged. This chapter reads the recorded
JSONs and lays out the axis: what doubled frames cost, and what they did
not change.

**Before this:** [stage 04's longer-sequences run](../) and stage 02's
8-frame baseline.

## The axis, read

The run ([record](runs/2026-08-06-frame-axis.md)) reads the recorded JSONs:

| seed | 8-frame MSE | 16-frame MSE | 16-frame exact-match | 16-frame cost |
|---|---:|---:|---:|---:|
| 0 | 0.0804 | 0.0818 | 0.087 | 567s |
| 1 | 0.0865 | 0.0859 | 0.140 | 709s |
| 2 | 0.0882 | 0.0892 | 0.333 | 705s |
| mean | 0.0851 | 0.0856 | — | ~660s |

## Two readings

**Reconstruction quality holds; the metric that moves is exact-match.**
Doubling frames leaves lm_completion MSE inside seed noise (0.0851 vs
0.0856 mean), but exact-match goes from a 2.7-point seed spread at 8 frames
to a 24.6-point spread at 16 — a genuinely noisier metric at the harder
scale, reported as an honest observation rather than explained away. The
pixel metric and the token metric disagree about how hard the task got.

**Cost grows ~4x for a 2x frame count, and the tokenizer stays the binding
constraint.** 152.5s to ~660s mean is more than the codec's roughly-linear
prediction, consistent with attention cost growing faster than linear. The
verdict stays MET — margin 0.0329 vs 0.0074 spread — but the cost and
quality reads together say the constraint is capacity (per-frame token
representation), not compute.

## Evidence boundary

The committed stage-02 (8-frame) and stage-04 (16-frame) seed JSONs, three
seeds each, one recipe; it reads those artifacts and does not re-train. The
wall-clock numbers are CPU-lane and include the stage's recorded system
variance.

## Check your mental model

Answer each before opening it.

**1. MSE barely moves from 8 to 16 frames. Why does the chapter still call
the axis a real cost?**

<details>
<summary>Answer</summary>

Because cost has more than one axis. Reconstruction quality holds, but
exact-match becomes far noisier (2.7-point to 24.6-point seed spread) and
wall-clock grows ~4x. A 2x frame increase bought ~2x of nothing on the
pixel metric while paying 4x in time and destroying token-level
reliability — that is the honest price of the harder scale.

</details>

**2. What does "the tokenizer, not compute, is the binding constraint" mean
for a next step?**

<details>
<summary>Answer</summary>

It points the next stage at the codec, not the sequence model. There is
wall-clock headroom left (max 39.4% of the ceiling), so adding compute
would not fix the exact-match collapse — the limit is that one 64-entry
token per frame cannot carry the extra state a longer sequence needs.
Stage 05 tests that same capacity limit from the object-count side.

</details>

## Next

Back to [stage 04](../), or to
[stage 05 — multi-object](../../05-multi-object/) which holds the frame count
at 8 and adds scene complexity instead.
