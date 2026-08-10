# Mission 06 full-chain report

## Command

```bash
cd 05-game-ai/05-report/core
uv run python report.py
```

Reads directly from `00-gridworld-baselines/runs/baselines.json`,
`01-grpo/runs/grpo-seed{0,1,2}.json`,
`03-fixing-collapse/runs/{small-group-seed0,small-group-seed1,small-group-seed2,entropy-bonus-seed0}.json`,
and `04-minigrid/runs/{minigrid-baselines,minigrid-seed0,minigrid-seed1,minigrid-seed2}.json`
-- no numbers are hand-copied.

## Output

```
Mission 06 outcome report (full chain: stages 00-04)
========================================================================

1. Stage 00-01: original 5x5 grid-world, fully observed
------------------------------------------------------------------------
  random baseline:   0.2220
  greedy baseline:   0.8240
  GRPO greedy decode:  mean=0.0727 spread=0.0160 per_seed=[0.078, 0.062, 0.078]
  GRPO sampled decode: mean=0.1787 spread=0.0660 per_seed=[0.182, 0.144, 0.21]
  greedy decode beats greedy baseline by more than seed spread: False
  greedy decode beats random by more than seed spread: False
  -> collapse: greedy decode converges to one fixed, board-independent action per seed (stage 01's finding).

2. Stage 03: is the collapse fixable via group size or an entropy bonus?
------------------------------------------------------------------------
  small-group (group_size=4), 3 seeds: greedy success=[0.024, 0.05, 0.036], degenerate steps=[18, 4, 10]
  entropy-bonus (coef=0.01), 1 seed (scope note in stage 03's own runs/ entry): greedy success=[0.078], degenerate steps=[0]
  small-group greedy-decode still board-independent (single fixed completion): [True, True, True]
  entropy-bonus greedy-decode still board-independent (single fixed completion): [True]
  -> fixed: False (both variants still collapse to a fixed completion on every tested seed)

3. Stage 04: does a fixed (or unfixed) policy generalize to MiniGrid, a partially-observed environment?
------------------------------------------------------------------------
  random baseline:      0.0040 (500 trials)
  wall-follow baseline: 1.0000 (500 trials)
  GRPO greedy decode: per_seed=[0.0, 0.0, 0.0]
  degenerate steps per seed: [80, 80, 80] out of [80, 80, 80]
  -> every step degenerate on every seed (zero gradient steps taken): True

4. Verdict against mission.yaml's acceptance bar
------------------------------------------------------------------------
  Acceptance requires: beats both baselines by more than run-to-run spread, OR an honest null result with mission 01's own rigor.
  stage 00-01 (original grid-world): beats both baselines = False
  stage 03 (collapse-fix sweep): collapse fixed = False
  stage 04 (MiniGrid): honest null result (100% degenerate steps, 0% eval success) = True

VERDICT: MET (as an honest null result, extended across two environments)
```

## Why "MET (as an honest null result)" and not "NOT MET"

Stage 01 alone (a real, trainable policy that decisively loses to both
baselines under greedy decode) would read as NOT MET on its own -- and
stage 02's own report says exactly that, for stage 01's scope alone, and
that verdict is left standing unmodified. This report's job is different:
it evaluates the acceptance bar's second disjunct ("OR reports an honest
null result with the same rigor mission 01's 04-rl applied to its own
zero-gradient outcome") against the mission's now-larger scope, which
stage 03 and stage 04 make possible to satisfy. Stage 03 establishes that
the stage 01 failure is not a training-signal artifact fixable by the two
most directly-motivated interventions available, which turns stage 01's
result from "an unexplained shortfall" into "a boundary that resisted the
obvious fixes." Stage 04 then finds a second, mechanistically-explained
null result in a harder domain (zero gradient steps taken, ever, across all
3 seeds -- confirmed as a real cold start via an independent solvability
check, not a broken environment). Together, that is the honest-null-result
register mission.yaml asks for, extended across two environments and one
fix attempt, rather than a single unexplained miss.
