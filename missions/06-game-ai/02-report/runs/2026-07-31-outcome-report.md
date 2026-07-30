# Mission 06 outcome report

## Command

```bash
cd missions/06-game-ai/02-report/core
uv run python report.py
```

Reads stage 00's `../../00-gridworld-baselines/runs/baselines.json` and stage
01's `../../01-grpo/runs/grpo-seed{0,1,2}.json` directly -- no numbers are
copied by hand into this script, unlike mission 05's report stage, since
both upstream files are already structured JSON. Apple silicon laptop,
macOS 15.6.1. Repository HEAD at time of run: `b4e2280`.

## Full output

```
Mission 06 outcome report
========================================================================

1. Primary metric: GRPO policy vs both stage 00 baselines (success rate on 500 held-out grids)
------------------------------------------------------------------------
  random baseline:   0.2220  (stage 00, 500 trials, single deterministic-seed measurement)
  greedy baseline:   0.8240  (stage 00, 500 trials, single deterministic-seed measurement)
  GRPO (greedy decode): mean=0.0727  spread=0.0160  per_seed=[0.078, 0.062, 0.078]
  GRPO (sampled decode, T=1.0): mean=0.1787  spread=0.0660  per_seed=[0.182, 0.144, 0.21]

  greedy decode vs random: margin -0.1493 vs GRPO's own seed spread 0.0160 -> decisively loses to this baseline
  greedy decode vs greedy baseline: margin -0.7513 vs GRPO's own seed spread 0.0160 -> decisively loses to this baseline
  sampled decode vs random: margin -0.0433 vs GRPO's own seed spread 0.0660 -> within the noise band of this baseline
  sampled decode vs greedy baseline: margin -0.6453 vs GRPO's own seed spread 0.0660 -> decisively loses to this baseline

2. Compute
------------------------------------------------------------------------
  seed 0: 130.8s, CPU, 200 steps
  seed 1: 118.1s, CPU, 200 steps
  seed 2: 123.9s, CPU, 200 steps

3. Failure catalogue (mission.yaml guardrail: catalogued by category, not merely counted)
------------------------------------------------------------------------
  degenerate rollout groups (every completion in a step scored identically, zero gradient): [0, 0, 1] out of 200 steps per seed -- minor, unlike mission 01's arithmetic run where this was the dominant outcome
  board-independent policy collapse (greedy decode emits the same fixed action string on every held-out board, ignoring the prompt): 3/3 seeds -- seed 0: always 'RRRRRRRRRRRR', seed 1: always 'UUUUUUUUUUUU', seed 2: always 'LLLLLLLLLLLL'
  non-stabilizing training-time success (peak sampled success rate falls back by the final logged steps instead of holding): 3/3 seeds -- seed 0: peak=0.417 -> final-window mean=0.119, seed 1: peak=0.500 -> final-window mean=0.188, seed 2: peak=0.406 -> final-window mean=0.188

VERDICT: NOT MET
  This is not the same shape of outcome as mission 01's arithmetic null result: training took real gradient steps on 199-200 of 200 steps per seed (not a zero-gradient run), and the policy clearly learned legal-move formatting and some board sensitivity under sampled decode. But the deployed (greedy) policy decisively loses to both baselines on every seed, and even the more favorable sampled-decode reading does not beat either baseline outside its own seed-to-seed spread. Per mission.yaml's acceptance bar this is neither a win nor a qualifying null result -- it is reported as NOT MET, plainly, rather than reframed as inconclusive.
```

## What this run establishes

Mission 06's mission.yaml acceptance bar names two outcomes: beat both
baselines by more than the seed spread, or an honest null result in mission
01 04-rl's own zero-gradient register. Stage 01's real result is neither --
training clearly moved (199-200/200 gradient steps per seed, real
board-sensitivity under sampled decode) but the policy that resulted
decisively loses to both baselines under the decode mode a deployed system
would actually use. This report states that plainly as NOT MET rather than
stretching the null-result register to cover a result that is not, in fact,
zero-gradient.

## What this run does not establish

Whether a longer run, more rollouts per step, or a different reward shape
would let board-conditioning survive to greedy decode -- stage 01's own
`runs/2026-07-31-grpo-training.md` already states this is unexplored.
Nothing about the mission-level answer to "is RL worth trying here" beyond
this one architecture/step-budget/seed combination.
