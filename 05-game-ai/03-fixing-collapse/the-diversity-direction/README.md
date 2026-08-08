---
status: verified
level: applied
base: scratch
label: The diversity direction
verified: 2026-08-06
---

# The one direction the collapse sweep never tried

**Question:** [stage 03](../) swept two knobs — group size and an entropy
bonus — and concluded neither fix worked. It tried smaller groups and a weak
bonus. What happens when you move both knobs the other way: a *larger* group
and a *stronger* entropy bonus?

**Before this:** [stage 03's collapse sweep](../), including its verdict.

## The two missing cells of the grid

The stage's sweep found small groups make degeneracy worse (18/4/10
degenerate steps vs the baseline's 0/0/1, with greedy success falling to
0.024-0.050) and a 0.01 entropy bonus changes nothing (0.078, same as
baseline). It concluded neither direction worked. The extension runs the
same two knobs in the opposite direction — group 16, and entropy 0.05 — on
the same grid-world, same reward, same loop
([run record](runs/2026-08-06-sweep-extension.md)):

| Variant | Degenerate / 200 | Greedy success | Sampled success | Gap |
|---|---:|---:|---:|---:|
| baseline (group 8) | 0/0/1 | 0.078 | 0.182 | 0.104 |
| small-group (group 4) | 18/4/10 | 0.024-0.050 | 0.032-0.080 | ~0.01 |
| entropy 0.01 | 0 | 0.078 | 0.176 | 0.098 |
| **group 16 (new)** | 0 | **0.156** | 0.198 | 0.042 |
| **entropy 0.05 (new)** | 0 | 0.032 | 0.036 | 0.004 |

## Which knob actually moved

**A larger group is the fix that works.** Greedy success doubles from the
baseline's 0.078 to 0.156, and the greedy-to-sampled gap — the collapse
itself, the distance between what the policy does greedily and what it does
when sampled — halves from 0.104 to 0.042. The mechanism is diversity: a
group of 16 completions per prompt gives the reward statistic a wider
spread to normalize against, so the few successful rollouts get sharper
advantages instead of being averaged into a greedy-decode failure. The
original sweep never tested this cell, because smaller groups were the
hypothesis it started with.

**A stronger entropy bonus is the opposite of a fix.** At 0.05 the greedy
success falls to 0.032, below baseline, and the gap collapses to 0.004 — the
policy is uniformly wrong rather than greedily collapsed. The entropy term
spreads probability mass instead of concentrating it on the behavior that
wins, which is the wrong pressure for a policy that needs to commit to the
goal-achieving route.

The lesson is the one the mission's whole sweep was built to show: a null
result covers only the grid you ran. The verdict "neither fix worked" was
accurate for two cells and wrong about the knob — the direction not tested
is where the mechanism moved.

## The fix and its trade

The fix this detour isolates is group size, tested in the direction the
original sweep never ran: `group_size=16` doubles greedy success (0.078 to
0.156) and halves the greedy-to-sampled gap (0.104 to 0.042), because a
wider group gives the reward statistic a larger spread to normalize
against, so the few successful rollouts get sharper advantages. The trade
is compute: a group of 16 is twice the rollouts per prompt, and the
doubled greedy success sits on one seed — the detour names both the
one-seed boundary and the need for the full 3-seed treatment before any
claim. The stronger entropy bonus (0.05) is the counter-case: it spreads
probability mass instead of concentrating it, collapsing greedy success to
0.032 — the same knob, the wrong direction, which is the lesson the
two-cell null taught.

## Who owns this loop

- **The RL team** owns the group-size dial as a measured lever, and the
  one-seed boundary on this cell: the doubling is a promising direction,
  not a result, and the owner reports it as such.
- **The evaluation owner** owns the greedy-to-sampled gap as the
  collapse metric: the gap halving (0.104 to 0.042) is what says the fix
  acts on the collapse itself, not just on aggregate success.
- **The reward owner** owns the interaction this result implies: if
  wider groups fix the cold-start variance, the reward shape that
  produced the variance in the first place remains the deeper suspect,
  and the diversity finding is evidence for the reward's next iteration.

## Evidence boundary

One seed per new cell, on the same single 5x5 grid-world as the recorded
sweep; the baseline and small-group rows carry their recorded seed spreads.
It shows group 16 moving the collapse on this environment and this seed; it
does not show it generalizing across environments, seeds, or reward shapes,
and it does not explain *why* diversity helps beyond the advantage-spread
mechanism the group-relative trick already establishes.

## Check your mental model

Answer each before opening it.

**1. Why would a bigger group fix a greedy-decode collapse when a smaller one
made it worse?**

<details>
<summary>Answer</summary>

Because the advantage is a group statistic, and its sharpness depends on the
spread inside the group. A group of 4 nearly always produces all-loss or
all-win rollouts, so the statistic is degenerate or flat; a group of 16 is
far more likely to contain a successful rollout, giving the reward a real
spread to normalize against and the policy a concrete behavior to push
toward. Smaller groups shrink the very diversity the statistic needs.

</details>

**2. The entropy bonus at 0.05 keeps entropy high but kills success. What
does that combination say about what the policy needs?**

<details>
<summary>Answer</summary>

That the collapse is not a diversity shortage at the token level — the
policy already explores, it just does not concentrate on the winning route.
Entropy pressure fights the concentration GRPO is trying to create, so the
policy stays spread out and never commits to the goal-achieving behavior.
The knob that matters is diversity *inside the rollout group* (which the
reward can normalize), not entropy across the whole policy.

</details>

## Next

Back to [stage 03's sweep](../), or forward to
[stage 04's MiniGrid](../../04-minigrid/) where the cold-start null asks the
same question on a partially observed environment.
