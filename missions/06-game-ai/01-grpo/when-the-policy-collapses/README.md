---
status: verified
level: applied
base: scratch
label: When the policy collapses
verified: 2026-08-06
---

# The policy that learned one direction

**Question:** [stage 01's GRPO run](../) returned the mission's null result:
every trained seed collapses to a constant direction string. This chapter
reads the recorded seed JSONs and shows what the collapse looks like from
inside the run.

**Before this:** [stage 01's GRPO run](../) and its three recorded seeds.

## The collapse, read

The run ([record](runs/2026-08-06-collapse-read.md)) reads the committed
JSONs:

| seed | greedy-decoded success | policy emits |
|---|---:|---|
| 0 | 0.078 | `RRRRRRRRRRRR` on every held-out board |
| 1 | 0.062 | `UUUUUUUUUUUU` on every held-out board |
| 2 | 0.078 | `LLLLLLLLLLLL` on every held-out board |

## Two readings

**The policy learned to emit, not to navigate.** Each seed collapses to one
fixed direction string, repeated for the full action budget, on every
held-out board. That is the signature of a cold-start collapse: the policy
found a locally-rewarded mode — emitting a legal format gets format credit —
and never sharpened behavior that was absent to begin with. Group-relative
advantage is zero when every rollout in the group fails, which is why no
gradient step ever pulled it out.

**Greedy success (0.062-0.078) is below even the random floor.** Stage 00's
random baseline solves 22.2%; the trained policies solve roughly a third of
that. The collapse is not a near-miss of the greedy bar (82.4%) — it is
below the no-learning floor, which is exactly why the mission's report is an
honest null rather than a partial win. The training signal is real; the
behavior it could sharpen does not exist at cold-start scale.

## Evidence boundary

The three committed seed JSONs (200 steps each, one 5x5 board size, one
reward function); it reads those artifacts and does not re-train. It does
not claim no GRPO run could ever succeed — only that these three, under
this configuration, collapsed.

## Check your mental model

Answer each before opening it.

**1. The reward went up during training. Why does the chapter still call
the result a collapse?**

<details>
<summary>Answer</summary>

Because the reward that rose is mostly format credit — emitting a legal
action string gets partial reward even when it never reaches the goal.
The measured outcome, greedy-decoded success on held-out boards, is 0.062
to 0.078, below the random floor. The training curve and the mission metric
measure different things, and the mission is built around the second.

</details>

**2. Why is success below random (0.222) not just "training failed"?**

<details>
<summary>Answer</summary>

Because it is the specific, explainable failure the mission exists to
document: a policy can settle into a deterministic mode that is worse than
random because it stops exploring entirely. Random at least varies its
actions; the collapsed policy repeats one direction every episode, so it
can only win boards where that direction happens to work. That mechanism —
not generic "training didn't work" — is the null result.

</details>

## Next

Back to [stage 01](../), or to
[the report's verdict read](../../02-report/when-the-verdict-is-not-met/)
which turns this collapse into the mission's NOT MET.
