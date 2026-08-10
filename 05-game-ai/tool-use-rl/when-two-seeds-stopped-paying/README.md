---
status: verified
level: applied
base: scratch
label: When two seeds stopped paying
verified: 2026-08-06
---

# Why did two seeds stop paying for the tool?

**Question:** [stage 06](../) reports 1/3 seeds calibrated and 2/3 collapsed
to always-answer. The tool-use decision is a per-step rate — the fraction of
completions that paid for the tool — and reading that rate across training
shows the collapse arriving as a trajectory, not a verdict.

**Before this:** [stage 06's tool-use RL run](../) and its per-level
breakdown.

## The trajectories

The analysis ([run record](runs/2026-08-06-tool-rate.md)) reads the three
recorded histories' `tool_rate` at early, mid, and late training:

| seed | early | mid | late | outcome |
|---:|---:|---:|---:|---|
| 0 | 0.667 | 0.097 | 0.533 | calibrated |
| 1 | 0.700 | 0.000 | 0.032 | collapsed |
| 2 | 0.545 | 0.097 | 0.000 | collapsed |

## The reading

**The calibrated seed's rate oscillates; the collapsed seeds' rates die.**
Seed 0 pays for the tool at 0.67 early, dips to 0.10, and recovers to 0.53 —
the signature of a difficulty-conditioned policy that buys the tool when
the level asks for it and answers directly when it does not. Seeds 1 and 2
fall monotonically to 0.03 and 0.00 and stay there: they stop paying
entirely and answer at every level, the context-independent collapse the
recorded run's per-level breakdown names.

**The trajectory separates the outcomes before the verdict.** By mid-
training, seed 0 has already shown its recovery while seeds 1-2 sit at or
near zero. A final-success-only read misses that the divergence happened
early; the rate trajectory is the diagnostic that sees it.

**This is the diversity-direction lesson on the tool decision.** The
group-relative advantage can only sharpen a decision the rollouts still
vary on. When the policy's tool rate collapses to zero, its completions stop
separating, the group statistic has nothing to normalize, and the
calibration is gone — the same mechanism the collapse-sweep extension
measured for greedy-decode, now visible in a decision the mission actually
cares about.

## The fix and its trade

The fix is the trajectory diagnostic, not a training dial: reading
tool_rate at early, mid, and late training separates the outcomes before
the final verdict, because the divergence is visible by mid-training
(seed 0 recovers to 0.533 while seeds 1-2 sit at 0.03 and 0.00). The
trade is that the diagnostic sees the divergence without explaining it:
the reading names group-diversity as the candidate mechanism, not the
proof, and it explicitly does not claim a fix — the collapse is real and
recorded. The value is the same one the diversity-direction detour
measured for greedy decode: when the tool rate collapses, completions stop
separating, the group statistic has nothing to normalize, and the
calibration is gone — so the actionable lever is the reward variance the
rollouts still produce, owned by the reward/group-size dial, not by a
bigger final-eval.

## Who owns this loop

- **The evaluation owner** owns the trajectory read: a final-success-only
  metric misses that the divergence happened early, so the diagnostic is
  per-phase tool_rate, not the aggregate verdict.
- **The reward owner** owns the tool-cost balance the collapse responds
  to: the seeds differ in whether the outcome credit outweighed format
  credit, which is the lever a fix would pull.
- **The RL team** owns the mechanism claim's boundary: group-diversity is
  the candidate explanation, cross-linked to the diversity-direction
  measurement, and the reading keeps it a candidate rather than a proof.

## Evidence boundary

Three seeds, one environment, the stage's recorded run. It shows the
tool-rate trajectories and their early divergence; it does not explain why
the seeds diverged (the group-diversity mechanism is the candidate, not the
proof), and it does not claim a fix — the collapse is real and recorded.

## Check your mental model

Answer each before opening it.

**1. Seed 0's tool rate dips to 0.10 at mid-training and recovers. Why is
that a calibration signature rather than a collapse?**

<details>
<summary>Answer</summary>

Because it recovers: a difficulty-conditioned policy pays for the tool only
when the level needs it, so its rate fluctuates with the levels it meets.
The collapsed seeds' rates fall and stay near zero, which is a different
shape — a decision that died, not a decision that varies. The oscillation
is the signature of conditioning; the flat zero is the signature of
collapse.

</details>

**2. Why does a zero tool rate kill the GRPO update instead of just making
the policy answer directly?**

<details>
<summary>Answer</summary>

Because the group advantage needs variance in the rollouts to normalize
against. When every completion in a group answers directly, their rewards
are identical, the advantage is 0/0, and the group contributes no gradient —
so there is no pressure to rediscover tool use. The collapsed decision is
self-stabilizing under GRPO, which is why the collapse persists once it
arrives.

</details>

## Next

Back to [stage 06's tool-use RL](../), or to
[the diversity-direction chapter](../../03-fixing-collapse/the-diversity-direction/)
where the group-diversity mechanism this collapse runs on is measured.
