---
status: verified
level: applied
base: scratch
label: The collision that closed the gap
verified: 2026-08-06
---

# Disjoint seeds are not disjoint images

**Question:** [stage 00's dataset generation](../) splits train and eval by
seed range. This chapter reads the recorded run and asks why that is not
enough.

**Before this:** [stage 00's image-caption task](../) and its recorded
dataset run.

## The defects, read

The run ([record](runs/2026-08-06-collision-read.md)) reads the recorded
numbers:

| defect | value |
|---|---|
| pixel-identical train/eval collisions | 116 |
| second defect | eval single-shape bucket empty |
| fix | widen each shape's size and position space |

## Two readings

**The state space is small enough that collisions happen across seed
streams.** Train used seeds 0-1999, eval 100000-100399 — different streams,
different pseudo-random sequences — and still produced 116 pixel-identical
collisions. The image space is 4 cells x 3 shapes x 4 colors: small enough
that the same image renders under different seeds. That is why the
guardrail must check pixels, not seeds.

**The empty bucket is the defect a pixels-only check misses.** The
collision check caught the 116; the rejection-sampling fix that closed it
then silently emptied eval's single-shape bucket. Two failures, two
checks: the guardrail has to verify the distribution survived the fix, not
just that the collision count dropped to zero.

## Evidence boundary

The recorded dataset-generation run (2,000/400 split, one generator, one
fix). It reads that artifact; it does not re-generate and the collision
count characterizes this small state space.

## Check your mental model

Answer each before opening it.

**1. Why do different seeds still produce the same image?**

<details>
<summary>Answer</summary>

Because the image state space is finite and small: 4 cells x 3 shapes x 4
colors leaves only 48 states for a one-shape image. With hundreds of
draws, the generator revisits the same rendering under different seed
streams — the seed chooses a stream, not a unique image. The collision
check on rendered pixels is what catches what the seed ranges cannot
guarantee.

</details>

**2. Why is the empty bucket a second defect rather than the same one?**

<details>
<summary>Answer</summary>

Because it appears only after the first fix. The rejection-sampling change
that removed the 116 collisions also emptied eval's single-shape bucket —
a distribution change that the collision count would report as success.
The two checks answer different questions: "no shared images" and "the
eval distribution is still proportional to train's," and both must pass.

</details>

## Next

Back to [stage 00](../), or to
[why the leakage guardrail checks pixels, not seeds](../seed-vs-pixels/)
which reads the same stage's guardrail story.
