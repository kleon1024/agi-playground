---
status: verified
level: applied
base: scratch
label: When the axes compound
verified: 2026-08-06
---

# The fourth corner: 16 frames and 2 objects together

**Question:** [stage 06's longer-and-multi-object run](../) ran both hard
axes at once. This chapter reads the recorded JSONs and asks where the
difficulties compound.

**Before this:** [stage 06's run](../) and its recorded JSONs.

## The corner, read

The run ([record](runs/2026-08-06-axes-compound.md)) reads the recorded
rows:

| seed | LM MSE | frame-repeat | exact-match | verdict |
|---|---:|---:|---:|---|
| 0 | 0.1391 | 0.1998 | 0.000 | MET |
| 1 | 0.1375 | 0.1998 | 0.007 | MET |
| 2 | 0.1456 | 0.1998 | 0.007 | MET |

## Two readings

**In pixel space the axes do not add.** The 16-frame + 2-object MSE
(0.1375-0.1456) sits inside the range the second object alone already
cost (0.1429-0.1533) — doubling the frames is close to free once the
codec is per-frame. The two difficulties are additive in pixel space, not
multiplicative.

**In token space they compound to the floor.** Exact-match collapses to
0.000-0.007 — near zero — and its seed-to-seed spread collapses with it.
That reframes the noisy exact-match from earlier stages as a mid-range
artifact of an all-or-nothing metric, not a property of the task: once
the task is hard enough, exact-match has nowhere left to fall. The verdict
still closes MET at 22-27% of the ceiling, and the model-to-oracle gap
(0.0001 on one seed) says the tokenizer is what is missing.

## Evidence boundary

The recorded stage-06 JSONs (three seeds, one recipe, uncontended CPU
wall-clock). It reads those artifacts; it does not re-train.

## Check your mental model

Answer each before opening it.

**1. Why do the axes add in pixel space but compound in token space?**

<details>
<summary>Answer</summary>

Because they stress different stages. Frame count and object count both
load the per-frame codec, which is where pixel error accrues — so their
contributions add in MSE. Token identity is all-or-nothing: either the
sequence matches or it does not, so once the task is hard enough,
exact-match saturates at the floor regardless of which axis pushed it
there. The two metrics report different stages' stress.

</details>

**2. What does the near-zero oracle gap mean?**

<details>
<summary>Answer</summary>

That the sequence model is not the limit — the tokenizer is. The
model-to-oracle gap of 0.0001 on one seed means the LM's generation is
essentially as good as feeding the true tokens; the reconstruction error
is the codec's, before the LM even acts. The same conclusion as stages
04-05, now confirmed on the combined hardest corner.

</details>

## Next

Back to [stage 06](../), or to
[which axis costs the generation — and when does the metric hit zero](../when-the-metric-hits-zero/)
which reads the same runs' axis attribution.
