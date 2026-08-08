---
status: verified
level: applied
base: scratch
label: The answer-type-shaped edge
verified: 2026-08-06
---

# The API's edge is shaped like the answer type

**Question:** [stage 05's real-photo report](../) found the hosted API
dominates on real photographs. This chapter recomputes the per-type split
from the raw log and asks where the API's edge actually lives.

**Before this:** [stage 05's real-photo report](../) and its recorded log.

## The split, recomputed

The run ([record](runs/2026-08-06-type-edge-read.md)) reads the recorded
198-row log:

| answer type | accuracy |
|---|---:|
| yes/no | 51/80 (0.637) |
| other | 34/93 (0.366) |
| number | 6/25 (0.240) |

## Two readings

**The recomputation reproduces the recorded report exactly.** The report
quoted 63.7% on yes/no and 24.0% on number; the log's own rows produce the
same numbers, so the type split is the raw data's, not the report's prose.
That is the evidence-discipline check: a claimed per-type pattern must be
reproducible from the artifact it cites.

**The edge is strongest where the type is easiest, weakest where counting
is required.** The API reaches 0.637 on yes/no and falls to 0.240 on
number questions. The type split is where a future build could compete —
not head-on against the API's overall dominance, but on the number
questions where the API itself is weak.

## The fix and its trade

The fix is the artifact-traceability check: recompute the per-type split
from the raw log rows instead of trusting the report's quoted numbers. The
report's 0.637/0.366/0.240 could have been hand-copied or rounded; the
recomputation from the 198-row log producing the same numbers is the
evidence that the pattern is real and belongs to the data, not the prose.
The trade is that the check confirms the verdict without changing it — the
recomputation reproduces the recorded report (yes/no 0.637, number 0.240,
within rounding) and leaves NOT MET intact — but it changes what a future
build-vs-buy decision can target: the API is not uniformly dominant, and
the number questions where it falls to 0.240, close to the self-trained
arms, are the ground a targeted build could compete on instead of
competing head-on. The discipline the fix enforces is the repository's own:
a per-type claim traces to its rows, the same way every other claim traces
to its run.

## Who owns the loop

- **The evaluation owner** owns the artifact-traceability check: the
  recomputation from the raw log is an eval-standard gate that a claimed
  pattern must pass before it is reported as the pattern's evidence.
- **The model team** owns the where-to-compete read the type split
  produces: the number questions where the API is weakest are a targeting
  input for a future build, and the team owns the interpretation that a
  category-level edge is not yet a measured win.
- **The report owner** owns keeping the verdict stable: the recomputation
  confirms NOT MET and must not be read as an upgrade of the mission's
  answer.

## Evidence boundary

The recorded real-photo API log (198 questions, one model, one prompt).
It recomputes accuracy from that artifact; it does not re-call the API and
does not change the mission's NOT MET verdict.

## Check your mental model

Answer each before opening it.

**1. Why does the recomputation matter if the report already stated the
numbers?**

<details>
<summary>Answer</summary>

Because a claimed pattern is only as good as its artifact. The report's
63.7%/24.0% could have been hand-copied or rounded; recomputing from the
log rows and getting the same numbers is the check that the pattern is
real. The discipline is the same one the whole repository applies — a
number traces to its run, and a per-type claim traces to its rows.

</details>

**2. What does the type shape imply for a future build-vs-buy decision?**

<details>
<summary>Answer</summary>

That the API is not uniformly dominant. On number questions its accuracy
falls to 0.240 — close to the self-trained arms — so a targeted build that
specializes in counting could compete where the API is weakest instead of
competing head-on. The verdict stays NOT MET overall, but the type
structure is the evidence for where a different build might find ground.

</details>

## Next

Back to [stage 05's report](../), or to
[the build-vs-buy verdict, on real photos](../when-the-api-still-wins/)
which reads the same log's three-arm comparison.
