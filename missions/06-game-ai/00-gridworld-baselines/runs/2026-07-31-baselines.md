# Random and greedy baselines on the grid-world environment

## Command

```bash
cd missions/06-game-ai/00-gridworld-baselines/core
uv run python measure_baselines.py --trials 500
```

## Environment

Pure Python, no dependencies (no torch, no gymnasium) -- the environment
simulator and both baselines are deterministic given a seed. Apple silicon
laptop, macOS 24.6.0; wall-clock 0.02s for 1,000 episodes total (500 grids x
2 policies), since nothing here trains a model. Repository HEAD at time of
run: `51ac250`.

## What ran

500 independently sampled 5x5 grids (`sample_grid(rng, size=5, num_walls=4)`,
rejection-sampled for solvability via BFS), each policy given a 12-step
budget -- slack of 4 over the largest possible Manhattan distance (8) on a
5x5 board, to leave room for a real detour around a wall without being long
enough to make failure meaningless.

## Result

```
 random: 111/500 = 0.222  mean_steps_on_success=5.43
 greedy: 412/500 =  0.824  mean_steps_on_success=3.15
```

Greedy's one-step-lookahead beats random by a wide margin, as expected, but
is not saturated at 100% -- its one real failure mode (no memory of visited
cells, so a wall layout that requires a temporary detour *away* from the
goal traps it oscillating for the rest of the budget) fires often enough to
leave real room for a trained policy to beat it, not just tie it. Neither
baseline is degenerate (0% or 100%), which is the property mission.yaml's
guardrail actually cares about at this stage: an environment sized so a
training run in stage 01 can say something, whichever direction it goes.

## What this run does not establish

Whether a cold-start GRPO policy (a randomly initialized Transformer, per
this mission's own design) clears the bar to get a nonzero gradient at all
on this environment -- that is exactly the open question stage 01 exists to
answer, and mission 01's own null result on a different task is the reason
it is a real open question here, not a formality. Nothing about a larger
grid, a different wall density, or a different step budget; this one
configuration is what stage 01 trains and evaluates against.
