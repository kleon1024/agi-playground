---
status: verified
level: applied
base: scratch
label: When the cost grows faster
verified: 2026-08-06
---

# 4.3x cost for 2x frames

**Question:** [stage 04's longer sequences](../) doubled N_FRAMES from 8 to
16. This chapter reads the recorded runs and asks what the cost growth
actually was.

**Before this:** [stage 04's longer sequences](../) and its recorded JSONs.

## The growth, read

The run ([record](runs/2026-08-06-cost-growth.md)) reads the recorded
costs:

| | 8 frames | 16 frames |
|---|---:|---:|
| seed 0 | 153s | 567s |
| seed 1 | 151s | 709s |
| seed 2 | 154s | 705s |
| mean | 152s | 660s (4.3x) |

## Two readings

**Cost grows ~4x for a 2x frame count — more than the codec's linear
prediction.** Stage 03 predicted the codec's per-frame cost scales roughly
linearly, and the LM's attention cost grows with sequence length. The
measured 4.3x sits above pure linearity, consistent with the LM's
attention cost growing faster than linear (sequence length 9 -> 17
tokens). The cost axis is superlinear even at this toy scale.

**The verdict stays MET, so the axis is a cost finding, not a failure.**
LM completion mean 0.0856 vs frame-repeat 0.1185 is a margin 4.4x the
seed spread (0.0074), and the ceiling is used at 31.5-39.4% — real
headroom remains. The finding is the cost curve's shape: reconstruction
holds, cost outruns the frames, and the tokenizer is still the binding
constraint.

## Evidence boundary

The recorded stage-04 JSONs (three seeds, one recipe, CPU lane). It reads
those artifacts; it does not re-train.

## Check your mental model

Answer each before opening it.

**1. Why does cost grow faster than the frame count?**

<details>
<summary>Answer</summary>

Because two components have different scaling. The codec processes frames
roughly linearly, but the sequence model's attention cost grows with the
square of sequence length — at 16 frames the LM attends over 17 tokens
instead of 9, more than doubling its cost. The 4.3x measured sits between
the codec's linearity and the LM's quadratic term, which is the signature
of both contributing.

</details>

**2. What does the headroom buy downstream?**

<details>
<summary>Answer</summary>

Room for harder axes. At 39.4% of the ceiling max, stages 05-06 can add
scene complexity without a compute wall — and the mission's own follow-on
question ("longer sequences and/or multi-object scenes") is runnable
because the ceiling is not the constraint. The cost finding says watch
the superlinear growth; the headroom says it has not bound yet.

</details>

## Next

Back to [stage 04](../), or to
[doubling the frames: what the same recipe says at 16](../when-the-frames-double/)
which reads the same runs' quality side.
