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
hosted API's per-category floor (0.769 on the same type); the build-vs-buy
answer is unchanged. What the category read changes is the *diagnosis*: the
pathway is not failing because it cannot see, it is failing because what it
sees is too weak to beat a stock API call. Stage 01's seed-2 collapse is the
same story at the category level — that seed emits end-of-sequence
immediately on `total_count` questions specifically, scoring 0/100 there
while staying in line on every other category.

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
