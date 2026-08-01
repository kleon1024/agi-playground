# MiniGrid: baselines, a solvability check, and GRPO from a cold start

## Commands

```bash
cd missions/06-game-ai/04-minigrid/core
uv run --group game python baselines_minigrid.py
uv run --group game --group torch python train_minigrid.py --steps 80 --group-size 4 --max-steps 10 --block-size 768 --eval-trials 100 --seed 0
uv run --group game --group torch python train_minigrid.py --steps 80 --group-size 4 --max-steps 10 --block-size 768 --eval-trials 100 --seed 1
uv run --group game --group torch python train_minigrid.py --steps 80 --group-size 4 --max-steps 10 --block-size 768 --eval-trials 100 --seed 2
```

CPU only, Apple silicon laptop, macOS 15.6.1. `MiniGrid-Empty-6x6-v0`,
`max_steps=10`.

## Solvability check (this is not an unsolvable environment)

Before training, two independent checks confirmed the task is solvable
within the 10-step budget:

- A hand-scripted 9-action sequence reaches the goal (reward greater than 0)
  across layout seeds 0-4.
- `run_wall_follow` (`baselines_minigrid.py`): if the cell directly ahead is
  open, move forward, else turn right. **500/500 = 100% success.**

`run_random` (uniform choice over forward/left/right, same 500 trials):
**2/500 = 0.4% success.** A random policy essentially never reaches the
goal in 10 steps in this room -- most random walks turn in place or run
into a wall repeatedly rather than committing to a heading and holding it.

Full baseline output: `minigrid-baselines.json`.

| Baseline | Trials | Successes | Success rate |
|---|---|---|---|
| random | 500 | 2 | 0.004 |
| wall-follow | 500 | 500 | 1.0 |

## GRPO training result

| Seed | Steps | Degenerate steps | Greedy success | Sampled success | Wall-clock |
|---|---|---|---|---|---|
| 0 | 80 | 80 | 0.0 | 0.0 | 31.8s |
| 1 | 80 | 80 | 0.0 | 0.0 | 32.1s |
| 2 | 80 | 80 | 0.0 | 0.0 | 31.8s |

**Every one of the 80 x 3 = 240 training steps across all 3 seeds was
degenerate** (all rollouts in the group scored the same reward, so GRPO's
group-relative advantage is exactly zero and no gradient step was taken --
`std(rewards) < 1e-6`, the same skip condition every other stage in this
mission uses). `history` is empty in all three run files because a record
is only logged on a non-degenerate step. Both greedy and sampled eval
success are exactly 0.0 on all 3 seeds -- the randomly-initialized policy
never reached the goal in evaluation either.

Full per-seed JSON: `minigrid-seed0.json`, `minigrid-seed1.json`,
`minigrid-seed2.json`.

## Why this happened (not a bug)

The random baseline explains it directly: a random policy succeeds 0.4% of
the time in this room within 10 steps. With `group_size=4`, the chance that
even one rollout in a group reaches the goal is roughly `1 - (1-0.004)^4 ≈
1.6%`, and GRPO needs *at least one success and one failure in the same
group* to get a nonzero-variance reward signal to learn from. At a
randomly-initialized policy's baseline success rate, most groups of 4 draw
either zero successes (near-certain) -- the observed outcome, 240/240 times.

This is the same boundary mission 01 named for the fully-observed
grid-world (a policy with no initial signal cannot be pushed by a
reward it never observes a variance in) recurring in a second, harder,
partially-observed domain: MiniGrid's egocentric 7x7 view and
closed-loop interleaved rollout make the exploration problem harder than
the fully-observed board, not easier, and the training data confirms it
mechanically rather than by assumption.

## Scope note

`group_size=4` and `steps=80` (vs. stage 01/03's `group_size=8`,
`steps=200`) were chosen to keep each seed's wall-clock under the mission's
declared 30-minute-per-seed local ceiling; actual wall-clock came in at
~32s/seed, well under budget, so the low step count is not itself the
reason no gradient step was ever taken -- the near-zero random-policy
success rate is. Whether a longer run, a larger group size, or a shaped
(non-sparse) reward would eventually produce a non-degenerate step was not
tested here; see the stage README for what this does not establish.
