---
status: verified
level: applied
base: scratch
label: The zero-failure taxonomy
verified: 2026-08-06
---

# Zero failures is a real result, not a gap

**Question:** [stage 04's failure taxonomy](../) sorts every real attempt
into categories. This chapter reads the recorded catalogue and asks what
the harness arm's all-zero rows mean.

**Before this:** [stage 04's failure taxonomy](../) and its recorded
catalogue.

## The taxonomy, read

The run ([record](runs/2026-08-06-taxonomy-read.md)) reads the recorded
matrix:

| category | harness (18) | no-harness (18) |
|---|---:|---:|
| resolved | 18/18 | 4/18 |
| target_still_failing | 0/18 | 12/18 |
| regressed | 0/18 | 0/18 |
| tampered | 0/18 | 0/18 |
| no_tests_ran | 0/18 | 0/18 |
| timeout | 0/18 | 2/18 |

## Two readings

**The harness arm's zero-failure rows are the point, not an artifact.**
With tool access, test feedback, and up to 25 steps, no tier produced a
single failure category — every attempt resolved. That is a genuine result
about the harness: its failure surface, at this task scale, is empty. The
taxonomy is not missing categories; the harness genuinely did not exercise
them.

**The no-harness arm is where the taxonomy earns its keep.** 12/18
target_still_failing and 2/18 timeouts give the categories their content —
the same tasks, without tools, fail in a catalogued pattern. The contrast
is the stage's argument: failures are a property of the loop, not the
task, and the taxonomy is what makes that legible.

## Evidence boundary

The recorded taxonomy (36 real attempts: 18 harness, 18 no-harness, the
categories `scoring.score` already assigns). It reads that artifact; it
does not re-run any model and the zero rows characterize this task scale.

## Check your mental model

Answer each before opening it.

**1. Why is an all-zero failure row still evidence?**

<details>
<summary>Answer</summary>

Because it answers a question. The mission's guardrail asks for failures
catalogued by category; the harness arm's answer is "no failures occurred"
— a real, bounded claim about the harness at this scale, not a missing
measurement. If the taxonomy were incomplete, the categories would be
missing from the no-harness arm too, and they are not.

</details>

**2. What does the harness-vs-no-harness contrast prove?**

<details>
<summary>Answer</summary>

That the failure mode is the loop, not the task. The same 18 attempts
resolve 18/18 with tools and fail 12/18 without them — target_still_failing
is the dominant no-harness category and absent from the harness arm. The
taxonomy turns that into a per-category contrast instead of a single
"harness is better" headline.

</details>

## Next

Back to [stage 04](../), or to
[when the patch cannot even be applied](../when-the-patch-cannot-apply/)
which reads the same catalogue's apply-failure side.
