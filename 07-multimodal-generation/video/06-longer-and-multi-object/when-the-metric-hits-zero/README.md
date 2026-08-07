---
status: verified
level: applied
base: scratch
label: When the metric hits zero
verified: 2026-08-06
---

# Which axis costs the generation — and when does the metric hit zero?

**Question:** the mission's generation stages sample a grid — frames (8,
16) by objects (1, 2) — and every corner passed its feasibility verdict.
This chapter assembles the four corners from the recorded runs to read the
frontier: which axis costs more, and where the token metric hits zero while
the pixel metric still holds.

**Before this:** the mission's generation stages and their recorded runs.

## The frontier, assembled

The run ([record](runs/2026-08-06-frontier-grid.md)) reads the four corners'
reconstruction MSE:

| corner | LM MSE | frame-repeat baseline |
|---|---:|---:|
| 8 frames x 1 object | 0.0804 | 0.1281 |
| 16 frames x 1 object | 0.0818 | 0.1185 |
| 8 frames x 2 objects | 0.1429 | 0.2193 |
| 16 frames x 2 objects | 0.1391 | 0.1998 |

## Two readings

**Objects are the dominant axis, not length.** Going 1 to 2 objects roughly
doubles both MSEs (LM 0.080 to 0.143), while 8 to 16 frames barely moves
anything (0.0804 to 0.0818 at one object). The multi-object corner's cost is
occlusion and object interaction — the harder problem the single-object
stages never exposed — and it is the axis the feasibility frontier is set
by.

**The LM beats frame-repeat everywhere, and at the 16x2 corner the exact-
match rate is 0.00%.** Feasibility holds on the whole grid, and the zero
exact-match is the wrong-tokens lesson at the limit: no generated token
sequence matches the oracle's, yet the reconstruction still clears the
baseline (0.139 vs 0.200). The token metric has hit zero; the pixel metric
is what the verdict rests on.

## Evidence boundary

Four recorded corners, seed 0 each, the stages' own runs. It reads the
frontier's shape and the axis dominance on this grid; it does not claim the
dominance transfers beyond the tested corners, and it does not re-train.

## Check your mental model

Answer each before opening it.

**1. Why does adding a second object cost more than doubling the length?**

<details>
<summary>Answer</summary>

Because length is a scaling axis — more of the same frame-generation task —
while a second object introduces occlusion and interaction: the model has
to represent which object is in front, and the codec has to reconstruct
both through their overlap. The reconstruction error roughly doubles
(0.080 to 0.143) for the object axis and moves 0.001 for the length axis,
which is the frontier's answer: the hard part is objects, not duration.

</details>

**2. The exact-match rate is 0.00% at the 16x2 corner. Why is the verdict
still MET?**

<details>
<summary>Answer</summary>

Because the verdict rests on reconstruction against the frame-repeat
baseline, not on token identity. The LM never predicts the oracle's exact
token sequence at this corner, but its wrong tokens reconstruct to 0.139
MSE, comfortably below the baseline's 0.200 — the codebook carries
near-equivalent tokens, so the pixel output is still right where the token
identity is always wrong. The metric that hit zero is measuring something
the feasibility question does not depend on.

</details>

## Next

Back to [the 16x2 stage](../), or to
[the cost report](../../03-report/) where every corner's verdict is held
against the mission's ceiling.
