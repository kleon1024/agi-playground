---
status: verified
level: applied
base: scratch
label: The solvability check
verified: 2026-08-06
---

# The task is solvable — so the cold start is the training

**Question:** [stage 04's MiniGrid run](../) recorded a total cold start.
This chapter reads the recorded solvability checks and asks what they
establish about the null result.

**Before this:** [stage 04's MiniGrid run](../) and its recorded checks.

## The checks, read

The run ([record](runs/2026-08-06-solvability-read.md)) reads the recorded
numbers:

| check | result |
|---|---|
| hand-scripted 9-action sequence | reaches the goal (layout seeds 0-4) |
| wall-following policy | 500/500 = 100% success |
| random policy | 2/500 = 0.4% success |

## Two readings

**The task is solvable within the budget — twice, independently.** A
hand-scripted 9-action sequence reaches the goal, and a trivial
wall-following policy solves 100% of 500 trials. The environment is not
the problem: a fixed 10-step budget is enough, and the room is
navigable. That is the precondition that makes the cold start
attributable to training rather than to an unsolvable task.

**The random floor makes the gap concrete.** Random succeeds 0.4% — a
policy that commits to no heading basically turns in place. The wall-
following 100% against the random 0.4% brackets what the task requires:
commit to a direction and hold it. A GRPO policy that cannot reach even
the random floor's neighborhood is failing at something more basic than
navigation.

## Evidence boundary

The recorded MiniGrid run (MiniGrid-Empty-6x6-v0, max_steps 10, 500-trial
baseline checks, three training seeds). It reads that artifact; it does
not re-run the environment.

## Check your mental model

Answer each before opening it.

**1. Why must the solvability check come before the training verdict?**

<details>
<summary>Answer</summary>

Because a null result is only a finding if the task is not the cause. If
the 10-step budget were impossible, the GRPO failure would be the
environment's fault and say nothing about the method. The two independent
proofs (hand-scripted sequence, wall-following 100%) rule that out, so the
cold start is attributable to the training — the check is what makes the
null meaningful.

</details>

**2. What does the 100%-vs-0.4% contrast imply for the policy?**

<details>
<summary>Answer</summary>

That the task rewards commitment: a deterministic heading reaches the goal,
random turning does not. The GRPO policy's total collapse means it learned
neither — it is not at the random floor, it is below any useful behavior.
The baseline pair is the scale against which the trained policy's 0%
success is measured, which is what makes "total cold start" precise.

</details>

## Next

Back to [stage 04](../), or to
[why the cold start is total on MiniGrid](../when-the-cold-start-is-total/)
which reads the same run's training side.
