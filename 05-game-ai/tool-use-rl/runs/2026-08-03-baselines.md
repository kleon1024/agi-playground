# Fixed baselines and the calibrated-reference headroom, tool-use decision task

## Command

```bash
cd 05-game-ai/06-tool-use-rl/core
uv run python measure_baselines.py --trials 5000
```

Pure Python, no dependencies (no torch) -- the environment, both fixed
baselines, and the accuracy model are deterministic given a seed. Apple
silicon laptop, macOS 24.6.0; wall-clock 0.024s for 10,000 episodes total
(5,000 problems x 2 policies), since nothing here trains a model.
Repository HEAD at time of run: `d48fe02`.

## What ran

5,000 independently sampled problems (`sample_problem`, uniform over the 5
difficulty levels, 1-5 digit operands, addition or multiplication), scored
against each of the two required fixed policies -- `never_tool` (always
emits `A`, answers directly every time) and `always_tool` (always emits `T`,
invokes the calculator every time) -- using the same `compute_reward` stage
06's GRPO training scores its own rollouts against.

## Result

```
 never_tool:  mean_reward=0.8654  per_level={1: 1.173, 2: 1.022, 3: 0.879, 4: 0.715, 5: 0.552}
 always_tool: mean_reward=0.9000  per_level={1: 0.900, 2: 0.900, 3: 0.900, 4: 0.900, 5: 0.900}
 calibrated-oracle (reference, with format term): mean=0.9780
```

`always_tool` beats `never_tool` on the overall mean (0.900 vs 0.865) only
because 3 of the 5 difficulty levels (3, 4, 5) favor paying the tool's cost
-- `never_tool`'s per-level numbers fall from 1.173 at level 1 to 0.552 at
level 5, crossing `always_tool`'s flat 0.900 between levels 2 and 3, exactly
where `reward.py`'s `simulated_accuracy` docstring places the threshold.
Neither fixed baseline reads the difficulty label in the prompt at all --
`never_tool` pays the cost of never invoking the tool even on level 5, where
it is worth it; `always_tool` pays the tool's fixed cost even on level 1,
where it is not.

The calibrated-oracle reference (not one of the two required baselines --
it sees `simulated_accuracy` directly, which a real policy cannot) always
takes whichever action has the higher expected value at each level:
`max(0.97, 0.70)`, `max(0.82, 0.70)`, `max(0.70, 0.70)`, `max(0.70, 0.70)`,
`max(0.70, 0.70)` for levels 1-5, averaging 0.778 outcome-only or 0.978 with
the +0.2 format term both fixed baselines' clean completions also receive.
That states the real headroom: **0.078 over `always_tool`, 0.1126 over
`never_tool`** -- real room for a policy that reads the difficulty label
and discriminates by it to beat both.

## What this run does not establish

Whether a cold-start GRPO policy (a randomly initialized Transformer, the
same starting point every prior stage in this mission uses) can actually
learn to place its decision at this threshold -- that is the training run
this stage's own README and `runs/2026-08-03-grpo-training.md` report on.
Nothing about a different `TOOL_COST`, a different accuracy-model slope, or
a distribution over difficulty levels other than uniform; only this one
configuration is what the training run below is scored against.
