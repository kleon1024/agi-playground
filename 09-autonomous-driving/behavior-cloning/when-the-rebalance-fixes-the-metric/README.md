---
status: verified
level: applied
base: scratch
label: When rebalancing fixes the metric
verified: 2026-08-08
---

# Rebalancing fixed the metric, not the policy

**Question:** stage 03's 0.883 steer accuracy is an average over a demo set
that is 76% straight frames. When the rare dodge and brake classes are
rebalanced — the standard fix for a skewed label — does the open-loop metric
improve, and does that improvement transfer to the loop stage 04 actually
scores?

**Before this:** [stage 03 — behavior cloning](../) and its clone run.

## What rebalancing changes, executed

The run ([record](runs/2026-08-08-imbalance-rebalance.json)) trains three
clones from the same 8,366-frame demo set: the shipped procedure, a
class-weighted steer loss (inverse class frequency), and per-epoch
oversampling of the rare steer classes to majority size. Each is then
measured open-loop on the 7,432 held-out eval frames and in the loop on the
same 50 scenarios stage 04 uses.

The imbalance first, from the demo set:

| steer class | demo frames | share | weighted-loss weight |
|---|---|---:|---:|
| left | 1,003 | 12.0% | 2.780 |
| center | 6,353 | 75.9% | 0.439 |
| right | 1,010 | 12.1% | 2.761 |

Open loop, per-class recall and precision on dodge frames (steer left or
right), conditioned also on frames with an obstacle within 8 m ahead:

| variant | steer acc | joint acc | dodge recall | dodge precision | near dodge recall | near dodge precision |
|---|---:|---:|---:|---:|---:|---:|
| shipped checkpoint | 0.8827 | 0.7718 | 0.602 | 0.959 | 0.551 | 0.976 |
| base re-run | 0.8828 | 0.7684 | 0.699 | 0.855 | 0.664 | 0.793 |
| weighted loss | 0.747 | 0.6512 | 0.933 | 0.522 | 0.880 | 0.490 |
| oversampled | 0.7927 | 0.6759 | 0.900 | 0.583 | 0.792 | 0.613 |

In the loop, completion and collision over the same 50 scenarios:

| variant | completion | collision |
|---|---:|---:|
| shipped checkpoint | 0.28 | 0.72 |
| base re-run | 0.28 | 0.72 |
| weighted loss | 0.32 | 0.68 |
| oversampled | 0.44 | 0.56 |

Transfer against the base clone: seeds the base failed and the variant
completed ("recovered") and the reverse ("regressed"):

| variant | recovered seeds | regressed seeds |
|---|---|---|
| weighted loss | 110, 135 | none |
| oversampled | 109, 110, 111, 122, 135, 146, 147, 148 | none |

## The reading

The open-loop metric does not order the loop. The weighted clone has the
best dodge recall (0.933) and near-obstacle recall (0.880), yet it lifts
completion only 0.28 to 0.32; oversampled, with the lower recall (0.900 and
0.792), lifts completion to 0.44 and recovers eight seeds against two. The
reason is precision. Per-row dodge recall is measured on the expert's own
frames, where a dodge is exactly what the expert did. In the loop the
weighted clone fires dodge-plus-brake early and imprecisely — its dodge
precision collapses to 0.522 and near-obstacle precision to 0.490 — so it
starts a dodge, brakes, cuts back, and still collides on most obstacle
seeds. The loop rewards precision: a false-positive dodge costs the same
episode as a miss.

Oversampling makes the policy commit. On the eight recovered seeds its
episodes jump from roughly 40 steps to 119–129, lateral excursion reaches
0.5–0.9 m, and non-zero steering rises to match the expert's behavior on
those tracks (expert mean lateral offset 0.447 m over 148.6 steps). The
extra steering is dodge-shaped, not wander-shaped: on the 14 easy seeds the
base clone already completes, the oversampled clone keeps its mean lateral
offset at 0.081 m, near the expert's 0.089 m on the same subset — the
deviation is confined to the seeds where the expert itself dodges. The
trade is the flip side: oversampled steering accuracy drops from 0.883 to
0.793 and dodge precision from 0.959 to 0.583 — it now dodges where the
expert would not.

This is the precision–recall framing He and Garcia give imbalanced
learning: rebalancing moves the operating point along the precision–recall
curve, and which point the loop needs is a question the open-loop metric
cannot answer. The base re-run matters for the comparison: it reproduces
the shipped checkpoint (0.8828 steer accuracy, same 0.28 completion), so
the three clones differ only in label treatment, and the shipped artifact
is a faithful reproduction of the stage-03 procedure.

## The fix and its trade

The fix is to choose the rebalance by the loop's operating point, not by
open-loop recall: oversampling, which preserves the expert's action mix per
episode and biases the policy toward committing, beats class weighting,
which buys recall by destroying precision. The trade is that every rebalance
is a precision-for-recall exchange: oversampled dodge precision falls from
0.959 to 0.583 and steer accuracy from 0.883 to 0.793, and on a real stack
those false-positive dodges are sudden maneuvers a safety case must clear —
the operating point is a system decision, not a training default. The
deeper fix is on-policy training that labels the states the learner
actually reaches, which the [open-loop-lies detour](../../04-closed-loop-eval/when-the-open-loop-lies/)
walks; that moves the boundary but does not remove the precision–recall
trade.

## Who owns the loop

- **The data owner** owns the demo imbalance: 76% straight frames is a
  property of the collection protocol, and both repairs start from it.
- **The model owner** owns the operating point: the choice of weight or
  oversample ratio is a precision-recall decision, and the loop's
  false-positive dodge cost must enter that choice.
- **The eval owner** owns measuring in the loop, not only on expert frames:
  the recall-vs-completion inversion is invisible to open-loop metrics.

## Evidence boundary

One simulator, one 8,366-frame demo set, one expert, 50 scenarios. The
measured inversion — open-loop dodge recall does not order in-loop
completion — is a property of this render's obstacle signal and the
expert's action distribution; another task changes the numbers, not the
mechanism. The precision-recall framing is attributed to He and Garcia
(IEEE TKDE 2009), not re-derived here. Numbers trace to
[`runs/2026-08-08-imbalance-rebalance.json`](runs/2026-08-08-imbalance-rebalance.json).

## Check your mental model

Answer each before opening it.

**1. Weighted loss has the best dodge recall. Why does it complete fewer
episodes than oversampling?**

<details>
<summary>Answer</summary>

Recall is measured on the expert's frames, where a dodge is what the expert
did. In the loop the weighted clone fires dodges early and imprecisely —
dodge precision 0.522, near-obstacle 0.490 — so it starts a dodge, brakes,
and cuts back into the obstacle's path; most obstacle seeds still end in
collision. Completion rewards precision: a false-positive dodge costs the
same episode as a miss. Oversampling produces a policy that commits — on
the eight recovered seeds it deviates 0.5–0.9 m and drives about 120
steps, matching the expert's maneuver on those tracks.

</details>

**2. How do we know the recovered seeds' extra steering is dodge-shaped and
not wander?**

<details>
<summary>Answer</summary>

On the 14 easy seeds the base clone already completes, the oversampled
clone keeps its mean lateral offset at 0.081 m, near the expert's 0.089 m
on the same subset. If the extra steering were wander, the easy-seed
lateral offset would grow too. The growth is confined to the seeds where
the expert itself dodges — the signature of a committed maneuver rather
than noise.

</details>

**3. What does the base re-run add that the shipped row does not?**

<details>
<summary>Answer</summary>

It is the same procedure re-run in the same script, so its 0.28 completion
and 0.8828 steer accuracy are directly comparable to the rebalanced
variants — the three clones differ only in label treatment. The shipped
checkpoint row is included to confirm the base re-run reproduces the
shipped artifact (0.8827 steer accuracy, same 0.28 completion); the
comparison table stands on the clones trained under identical conditions.

</details>

## Next

Back to [stage 03](../). The rebalanced policies are exactly the artifact
stage 04 scores in the loop, where the same policy's errors compound — that
failure mode is walked in
[when the open-loop score lies](../../04-closed-loop-eval/when-the-open-loop-lies/),
and the report's verdict under a different 50-scenario draw is tested in
[when the verdict survives resampling](../../06-report/when-the-verdict-survives-resampling/).
