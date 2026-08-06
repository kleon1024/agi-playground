---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: A real partially-observed environment
---

# What happens when GRPO's cold start meets partial observability?

**Question:** stages 00-03 used a 5x5 grid-world where the whole board fits
in one text prompt, so a single open-loop completion can plan an entire
episode before acting. MiniGrid never reveals more than a 7x7 patch in
front of the agent. Does the same GRPO loop, on the same architecture,
still learn anything once the policy has to act on partial information and
re-observe after every move -- and if not, why not?

**The artifact this stage produces** is a genuinely new rollout mechanism
for partial observability (not just a rerun of stage 01's loop on a new
environment), plus a real, mechanistically-explained null result.

**Before this:** [stage 03](../03-fixing-collapse/), which found no fix
for stage 01's greedy-decode collapse via group size or an entropy bonus,
on the original fully-observed board.

## Why the fully-observed rollout loop does not carry over

In the 5x5 grid-world, the model sees the entire board once and generates
a whole action sequence in one pass -- `token_logprobs` (stage 01's core)
assumes the completion is one contiguous span right after a fixed prompt.
MiniGrid's `image` observation only ever covers the cells the agent could
plausibly see from where it is standing: a real partially-observed
environment. The policy must act on what it currently sees, the
environment returns a new observation, and the policy must act again --
there is no way to plan the whole episode before the first move.

This stage builds an interleaved rollout instead
(`core/train_minigrid.py`): the environment's own observation is rendered
to text and injected into the running sequence as non-optimized context
(exactly like the environment's true return value, never generated), one
forward pass samples exactly one action token, the action executes, and
the loop repeats. Only the action-token positions are scored and
optimized. Because those positions are now scattered through injected
observation text rather than forming one contiguous span, `grpo_loss`'s
slicing assumption breaks -- `masked_grpo_loss` replicates the identical
clipped-surrogate-plus-k3-KL math against an explicit list of action-token
positions instead. `Config`/`Transformer` (the architecture) are reused
unmodified from `../../01-language-model-agent/04-rl/core/grpo.py`, the
same as every other stage in this mission.

## Confirming the room is solvable before training

Before spending compute on training, two independent checks confirmed
`MiniGrid-Empty-6x6-v0` (10-step budget) is solvable: a hand-scripted
9-action sequence reaches the goal across 5 layout seeds, and a
wall-following heuristic (if the cell ahead is open, move forward, else
turn right) reaches the goal on **500/500** trials. A uniformly-random
policy over the three actions (forward, turn-left, turn-right) reaches it
on only **2/500 (0.4%)** trials in the same 10-step budget -- most random
walks turn in place or repeatedly walk into a wall rather than committing
to and holding a heading.

## What happened in training

3 seeds, 80 steps each, `group_size=4`, ~32s/seed wall-clock (well under
this mission's declared 30-minute-per-seed local ceiling):

| Seed | Degenerate steps / 80 | Greedy success | Sampled success |
|---|---|---|---|
| 0 | 80 | 0.0 | 0.0 |
| 1 | 80 | 0.0 | 0.0 |
| 2 | 80 | 0.0 | 0.0 |

**Every single training step, across all 3 seeds, was degenerate** -- every
rollout in every group of 4 scored the same reward (0), so GRPO's
group-relative advantage was exactly zero throughout, and not one gradient
step was ever taken. Both greedy and sampled evaluation success are
exactly 0.0 on all 3 seeds.

There is no greedy-versus-sampled gap to inspect here, because there is no
learned policy: [stage 01's decode comparison](../01-grpo/) needs a policy
that took at least one gradient step, and this run took none.

Full commands, per-seed numbers, and the mechanistic explanation:
[`runs/2026-08-01-minigrid-cold-start.md`](runs/2026-08-01-minigrid-cold-start.md).

## Why this is a real, explained finding, not an environment bug

The random baseline gives the mechanism directly: at a 0.4% per-episode
success rate, a group of 4 independent rollouts has roughly a 1.6% chance
of containing even one success -- so almost every group draws all-zero
rewards, exactly the degenerate condition GRPO's own variance check is
designed to skip. This is mission 01's own boundary ("GRPO cannot install
behavior a randomly-initialized policy never observes a reward variance
in") recurring in a second, harder domain: MiniGrid's partial observability
does not merely add noise, it removes the fully-observed board's implicit
scaffolding that let stage 01's policy stumble into *some* variance by
chance often enough to take 199-200/200 real gradient steps. Confirmed as a
genuine cold start rather than a broken environment or reward, since the
same environment is 100% solvable by a simple scripted heuristic.

## What this stage does not establish

Whether a longer run, a larger group size, a denser or shaped reward (e.g.
distance-to-goal shaping instead of sparse terminal reward), or a warm
start (pretraining on hand-scripted trajectories before GRPO) would produce
non-degenerate steps -- none of those were varied here. Whether this cold
start is specific to `MiniGrid-Empty-6x6-v0`'s exact size and step budget,
or would recur across the wider MiniGrid family. Whether the interleaved
rollout mechanism itself scales correctly once training does produce
gradient steps, since it never got the chance to be exercised under a real
update here.

**Next:** [stage 05](../05-report/) holds this result, stage 03's, and the
original stage 00-02 finding together against the mission's updated
acceptance bar.

A detour from here: [why is the cold start total on
MiniGrid?](when-the-cold-start-is-total/) — the sparsity gradient across
three environments: 22.2% baseline -> 1/200 degenerate, 0.4% -> 80/80,
~0% -> 200/200; degeneracy tracks baseline success by construction.

Another detour: [the task is solvable — so the cold start is the training](the-solvability-check/) — the recorded checks read: wall-following solves 500/500 while random solves 2/500, which is what makes the total cold start attributable.
