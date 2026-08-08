---
status: verified
level: applied
base: scratch
label: When the category breaks down
verified: 2026-08-06
---

# Where the NOT MET verdict hides the pathway's real signal

**Question:** [mission 05's report](../) returned `NOT MET` — the hosted API
dominates the self-trained vision pathway. That verdict is one aggregate
number. This chapter reads the same comparison at category granularity and
asks where the vision pathway's separation from text-only actually
concentrates.

**Before this:** [mission 05's report](../) and its recorded category
breakdown JSON.

## The comparison, read by category

The run ([record](runs/2026-08-06-category-breakdown.md)) reads the recorded
breakdown (`runs/category-breakdown.json`, from the report's own 3-seed
comparison) and tabulates vision minus text-only per category:

| category | vision | text-only | margin |
|---|---:|---:|---:|
| shape_color | 0.501 | 0.272 | +0.229 |
| total_count | 0.373 | 0.203 | +0.170 |
| presence | 0.574 | 0.514 | +0.060 |
| column_shape | 0.350 | 0.333 | +0.017 |
| shape_count | 0.432 | 0.422 | +0.010 |

## Two readings

**The aggregate verdict hides where the pathway's signal is real.** The two
largest margins are exactly the categories where the question cannot leak:
`shape_color` (+0.229) is unanswerable from question text alone, and
`total_count` (+0.170) needs counting pixels, not parsing words. The two
smallest margins (+0.017, +0.010) are the leak-prone types where the
question itself carries the answer. That pattern — separation concentrated
where the image is load-bearing — is the evidence that the vision pathway
conditions on pixels, not on memorized phrasing, and it survives inside a
verdict that is otherwise `NOT MET`.

**The verdict is still NOT MET, and the category read does not overturn it.**
The largest self-trained margin (+0.229 on `shape_color`) is still below the
hosted API's per-category accuracy on the same type (0.969); the build-vs-buy
answer is unchanged. What the category read changes is the *diagnosis*: the
pathway is not failing because it cannot see, it is failing because what it
sees is too weak to beat a stock API call. Stage 01's seed-2 collapse is the
same story at the category level — that seed emits end-of-sequence
immediately on `total_count` questions specifically, scoring 0/100 there
while staying in line on every other category.

## The fix and its trade

The fix is the per-category margin read: instead of one aggregate, compute
vision minus text-only inside each question type, because the *pattern* of
margins — not their size — is the evidence that distinguishes conditioning
on pixels from memorized phrasing. A pathway that improved on every
category equally could be explained by better text memorization; the
recorded concentration (shape_color +0.229, total_count +0.170, against
leak-prone types at +0.017 and +0.010) is the signature of real pixel
conditioning. The trade is that the category read changes the diagnosis,
not the verdict: the largest self-trained margin (+0.229) still sits below
the hosted API's per-category accuracy on the same type (0.969), so the
build-vs-buy answer stays NOT MET. What the fix buys is that the mission's
negative verdict no longer reads as "vision fusion does nothing" — it reads
as "the pathway sees, and what it sees is too weak to beat a stock API
call," which is the diagnosis a stakeholder needs before deciding what to
build next.

## Who owns the loop

- **The evaluation owner** owns the category taxonomy and its run: the
  per-category comparison is a separate artifact from the aggregate
  report, and the margin pattern is read from it, not asserted.
- **The report owner** owns keeping verdict and diagnosis separate: NOT
  MET for build-vs-buy, real pixel-conditioning signal for the mechanism,
  stated together without one erasing the other.
- **The model team** owns the collapse diagnosis the category read makes
  concrete: seed 2's 0/100 on total_count is a category-specific
  generation collapse (EOS emitted right after the question), which is a
  training-degradation story, not a broad architecture failure.

## Evidence boundary

The recorded category breakdown from the report's own 3-seed comparison; it
reads that artifact and does not re-train. The margins are vision-vs-text
only; the hosted API comparison is the report's recorded per-category
numbers. Nothing here changes the mission's `NOT MET` verdict.

## Check your mental model

Answer each before opening it.

**1. The aggregate verdict is NOT MET, yet this chapter calls the pathway's
signal "real." Why is that not a contradiction?**

<details>
<summary>Answer</summary>

Because the verdict and the diagnosis answer different questions. The
verdict asks whether building the pathway beats buying a hosted API call —
it does not, decisively. The category read asks whether the pathway learned
to use pixels at all — it did, and the separation concentrates exactly where
the question cannot leak. Both are true, and the second is why the mission's
`NOT MET` is a build-vs-buy answer rather than evidence that vision fusion
does nothing.

</details>

**2. Why does the pattern of margins matter more than their size?**

<details>
<summary>Answer</summary>

Because a pathway that improved on every category equally could be explained
by better memorization of question phrasing. The *concentration* — large
margins on `shape_color`/`total_count`, tiny margins on the leak-prone
types — is the signature of conditioning on pixels. The distribution is the
evidence, not any single number.

</details>

## Next

Back to [mission 05's report](../), or forward to
[the real-photo chain](../../03-real-photo-task/) where the same question is
asked of real photographs.
