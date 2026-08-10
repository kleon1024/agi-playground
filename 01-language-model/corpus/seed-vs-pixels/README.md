---
status: verified
level: applied
base: none
label: Seeds vs pixels
verified: 2026-08-06
---

# Why does a leakage guardrail need to check pixels, not seeds?

**Question:** [stage 00](../) splits its image set by seed range to keep
train and eval disjoint — and its recorded run found 116 pixel-identical
collisions anyway, then a second defect in the fix. This chapter reproduces
both mechanisms on the stage's own generator: why disjoint seeds do not
mean disjoint images, and why rejection sampling can silently distort a
dataset while passing the guardrail.

**Before this:** [stage 00's dataset generation](../), including its recorded
three-attempt history.

## The mechanism, reproduced

The reproduction ([run record](runs/2026-08-06-leak-reproduction.md)) runs
the current generator two ways:

| split | collisions | rejected | single-shape in eval |
|---|---:|---:|---:|
| naive (adjacent seeds, no rejection) | 17 | — | 126 |
| fixed (rejection past seed 100000) | 0 | 29 | 105 |

The fixed row exactly matches the recorded final run (rejected 29,
collisions 0, single-shape 105) — the generator is deterministic, and this
chapter confirms the pipeline as it stands today. The naive row is the
mechanism: **disjoint seed streams do not imply disjoint renders.** Seeds
randomize the RNG; renders live in a small pixel space. Draw a few thousand
images from a few thousand possible outcomes and the birthday paradox
guarantees repeats — a later eval draw lands on a train image even though
no seed was shared.

## The guardrail that passed and still broke the data

The recorded history adds the second defect, which this chapter does not
re-measure but reads as the lesson: rejection sampling fixed the collisions
(507 candidates rejected in the original narrow space) and, in doing so,
silently filtered the single-shape bucket out of eval entirely (0 single-
shape images). A guardrail can pass — collisions exactly zero — and the
dataset can still be broken in a way the guardrail was never built to see.
The current generator widened the state space at the source (per-shape size
and jitter, 48 -> 3,600 single-shape outcomes), which dropped the rejection
burden to 29 and restored the bucket (105 single-shape, proportional to
train's 696).

The lesson for any train/eval split: the check belongs on the thing that
leaks (pixels, text, embeddings), not on the generator that produces it
(seeds). And a rejection sampler is itself a distribution-altering step —
the count it rejects is the honest measure of how crowded the space is, and
the distribution after rejection must be checked, not assumed.

## The fix and its trade

The fix is the widened state space (per-shape size and jitter, 48 -> 3,600
single-shape outcomes) plus the distribution check, not the rejection
sampler alone. The reproduction prices the trade in rejection counts: the
fixed row rejects 29 candidates and restores the single-shape bucket (105,
proportional to train's 696), while the recorded narrow-space attempt
rejected 507 and filtered the bucket out of eval entirely. The naive row's
17 collisions show the pixel check still fires before the fix; the point is
that the check has to sit on the pixel representation, and the fix has to
sit on the generator's state space. Every fix trades something: a wider
space makes exact duplicates rarer but no longer impossible, and the
rejection count is the honest price of crowding — 29 rejections today
against 507 in the original space, which is exactly the difference the
distribution check exists to keep visible.

## Who owns the loop

- **The data pipeline** owns the guardrail key (pixels, not seeds) and the
  generator's state space; the reproduction that confirmed the pipeline
  "as it stands today" is a data-engineering artifact, not a modeling one.
- **The evaluation owner** owns the post-fix distribution check: the
  collision count answers "no shared images," and a separate assertion
  answers "the eval distribution is still proportional to train's." Both
  must pass, and the second is the one a pixels-only guardrail cannot see.
- **The report owner** owns disclosing the rejection burden (29 today, 507
  in the recorded original) as the honest crowding measure, so a later
  reader can see when a fix is papering over a crowded space.

## Evidence boundary

The naive row uses adjacent seeds on the current widened generator; the
recorded attempt-1's 116 came from the original narrow space and its own
ranges — the number is configuration-dependent, the mechanism is not. This
chapter reproduces the mechanism, not the historical bug's exact count.

## Check your mental model

Answer each before opening it.

**1. Train uses seeds 0-1999 and eval uses 2000-2399, so no seed is shared.
Why do 17 eval images still collide with train?**

<details>
<summary>Answer</summary>

Because the seed only picks the random draw; the rendered image lives in a
much smaller pixel space. Two different seeds can draw the same shape, color,
cell, size, and jitter, rendering identical pixels. With a few thousand
draws from a space of a few thousand outcomes, the birthday paradox makes
repeats expected — the collision is between images, not seeds, which is why
the guardrail has to hash pixels.

</details>

**2. Rejection sampling reports collisions = 0, yet the eval set is still
broken in the recorded narrow-space run. How?**

<details>
<summary>Answer</summary>

Because rejection removes candidates, and removing candidates changes the
distribution. In the narrow space, train's ~700 single-shape draws covered
nearly every single-shape state, so every fresh single-shape candidate
collided with train and was rejected — the sampler silently removed the
entire bucket from eval. The guardrail verified the property it was built to
check (no shared pixels) and could not see the property it was not built to
check (the eval distribution).

</details>

## Next

Back to [stage 00's generation](../), or forward to
[stage 01's vision fusion](../../01-vision-fusion/) where the disjoint,
distortion-free eval set is what the pathway is scored against.
