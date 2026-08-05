---
status: verified
level: applied
base: scratch
label: When the cold start is total
verified: 2026-08-06
---

# Why is the cold start total on MiniGrid?

**Question:** [stage 04](../) reports 0 gradient steps across all three
MiniGrid seeds — every rollout group degenerate. Mission 06's other
environments are not total: the grid-world trained with only 1/200
degenerate steps. The difference is a measured gradient, and it explains
when a cold start is total by construction.

**Before this:** [stage 04's MiniGrid cold-start run](../) and mission 01's
arithmetic null.

## The gradient, assembled

The analysis ([record](runs/2026-08-06-cold-start-sparsity.md)) reads the
recorded baselines and degeneracy counts:

| environment | random baseline success | GRPO degenerate steps |
|---|---:|---:|
| mission 01 arithmetic | ~0% (format) | 200/200 |
| mission 06 grid-world | 22.2% | 1/200 |
| mission 06 MiniGrid | 0.4% (2/500) | 80/80 per seed |

## The reading

**Degeneracy tracks baseline success.** The group-relative advantage is a
group statistic: it needs reward variance inside each rollout group, and
variance requires a policy that sometimes succeeds. Grid-world's random
policy reaches the goal 22.2% of the time, so most groups contain a mix of
winning and losing rollouts and the statistic moves (1/200 degenerate).
MiniGrid's random policy succeeds 0.4% — 2 in 500 episodes — so almost every
group scores identically zero and the advantage is 0/0 (80/80 degenerate).
Mission 01's arithmetic policy has a near-zero well-formed-completion rate
and is total (200/200).

**A total cold start is a property of the baseline, not a training failure.**
When the starting policy's success is near zero, no amount of group size or
entropy bonus can manufacture reward variance — the diversity-direction
chapter measured group-16 doubling greedy success where a 22.2% baseline
provided the variance; here there is nothing to diversify. The honest
response is the one stage 04 gives: report the null, and note that a denser
reward (not more training) is the lever a non-sparse variant would pull.

## Evidence boundary

The baseline and degeneracy numbers are the recorded runs' (grid-world
stage 00, MiniGrid stage 04, mission 01 stage 04); the sparsity gradient is
the assembled reading. It does not run new rollouts and does not test the
denser-reward hypothesis — that is the stage's own stated open question.

## Check your mental model

Answer each before opening it.

**1. Why can the grid-world train when its random baseline is only 22.2%,
but MiniGrid cannot at 0.4%?**

<details>
<summary>Answer</summary>

Because the group advantage needs variance within each rollout group, and
22.2% success means most groups of 8 contain at least one winning rollout —
the reward has a spread to normalize against. At 0.4%, almost every group
of 8 scores identically zero, the standard deviation is zero, and the
advantage is 0/0. The difference is not training; it is whether the baseline
policy occasionally produces the reward the statistic needs.

</details>

**2. What would make the MiniGrid cold start non-total, per this chapter's
logic?**

<details>
<summary>Answer</summary>

A reward signal the random policy sometimes earns — a denser reward, such
as progress toward the goal or sub-goal completion, instead of a binary
success bit. That gives the group statistic variance even when full success
is rare, which is the lever the stage names as its open question. More
training, bigger groups, or entropy bonuses cannot create variance the
reward does not provide.

</details>

## Next

Back to [stage 04's MiniGrid run](../../04-minigrid/), or to
[the diversity-direction chapter](../../03-fixing-collapse/the-diversity-direction/)
where the group-diversity mechanism this pattern runs on is measured.
