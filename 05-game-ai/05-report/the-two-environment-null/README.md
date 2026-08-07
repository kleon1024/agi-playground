---
status: verified
level: applied
base: scratch
label: The two-environment null
verified: 2026-08-06
---

# The null that repeated is the finding

**Question:** [stage 05's full-chain report](../) returned MET as an honest
null across two environments. This chapter reads the recorded report and
asks why the second environment changes the verdict's strength.

**Before this:** [stage 05's full-chain report](../) and its recorded
output.

## The verdict, read

The run ([record](runs/2026-08-06-two-env-read.md)) reads the recorded
report:

```
null result (100% degenerate steps, 0% eval success) = True
VERDICT: MET (as an honest null result, extended across two environments)
```

## Two readings

**The acceptance bar's second disjunct is what makes this MET, not NOT
MET.** Mission 06's contract allows either "beats both baselines" OR
"reports an honest null result with the same rigor mission 01 applied."
The grid-world alone was NOT MET; adding MiniGrid's total cold start
turns the two failures into one pattern, which is the null the contract
accepts.

**The repeated null is a stronger claim than either failure alone.** One
environment's collapse could be environment-specific; the same collapse
under a second environment (different task, different input format) says
the mechanism is in the training signal, not the domain. The verdict is
the pattern across two environments, which is why the report reads the
full chain rather than any single stage's number.

## Evidence boundary

The recorded full-chain report (stages 00-04 JSONs read mechanically, no
hand-copied numbers). It reads that artifact; it does not re-run any
training.

## Check your mental model

Answer each before opening it.

**1. Why is "MET as a null" not a contradiction?**

<details>
<summary>Answer</summary>

Because the mission's contract accepts two kinds of success: beating the
baselines, or honestly establishing that the training does not work at
this scale. The null result is the second disjunct, and it is "MET" only
because the report meets the null's rigor — declared bar, real runs, no
rescaling. A rigorous negative is a deliverable; NOT MET would misread
the contract.

</details>

**2. What does the second environment add that the first could not?**

<details>
<summary>Answer</summary>

Generalizability of the negative. The grid-world collapse could have been
a property of that one board and reward; MiniGrid's total cold start (a
different environment, a different input space) shows the same mechanism
fails again. Two environments make the null a pattern instead of an
anecdote, which is the difference between a result and a data point.

</details>

## Next

Back to [stage 05's report](../), or to
[the honest null, elevated to a verdict](../when-the-null-is-elevated/)
which reads the same report's contract side.
