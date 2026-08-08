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

## The fix and its trade

The fix is the state-space widening (each shape draws a size and a position
jitter, 48 -> 3,600 single-shape outcomes), with the distribution check as
the second gate. Rejection sampling was the tempting patch — it closed the
116 collisions — and it is exactly the patch that moved the failure: it
silently emptied the single-shape bucket, so the eval set scored a clean
guardrail pass while losing an entire category. The trade is priced in the
two numbers the run reports together: collisions at 0 and an eval
distribution proportional to train's (105 one-shape / 150 two-shape / 145
three-shape). A wider state space is not free — exact duplicates become
rarer rather than impossible, so the guardrail's zero is a property of the
space, and the two checks answer two questions that a single collision
count cannot: "no shared images" and "the eval distribution survived the
fix."

## Who owns the loop

- **The dataset generator** owns the state space; widening it is the
  durable fix, and the birthday-paradox math that made collisions
  inevitable at k=48 is the generator's design input, not an eval surprise.
- **The guardrail owner** owns both checks: the pixel-hash collision check
  that caught the 116, and the distribution check that would have caught
  the empty bucket. A guardrail that verifies one property and not the
  other is the failure this chapter exists to name.
- **The evaluation owner** owns reading the result: the collision count
  alone would report success, and the per-bucket distribution is the only
  number that shows the fix broke the data.

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
