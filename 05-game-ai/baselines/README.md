---
status: verified
level: applied
base: none
verified: 2026-07-31
label: Grid-world environment and baselines
---

# What does a policy have to beat before RL is worth trying?

**Question:** before training anything, this mission needs an environment
with a verifiable reward and two real baselines to compare against — the
same discipline mission 04 applied to routing and mission 05 applied to
vision. This stage builds the environment and measures both baselines for
real, so stage 01's GRPO run has an honest bar to clear.

**The artifact this stage produces** is one real solved episode:

```
.#...
...#.
..S.#
..#..
....G

greedy actions: RDDR (reached goal in 4 steps)
```

## Why a grid, not CartPole

`mission.yaml` names CartPole as one option and a small grid-world as the
other. This stage picks the grid for a concrete reason tied to how stage 01
will train: it reuses
[mission 01's `rollout_group`](../../01-language-model/04-rl/core/grpo.py)
unmodified, which samples one text completion per rollout with no
observation fed back to the policy mid-episode. CartPole's physics is
continuous and chaotic, so a policy that must commit to an entire action
sequence upfront, open-loop, cannot control it — any small drift compounds
with nothing to correct it. A grid with deterministic transitions has no
such problem: the whole board is already in the prompt, so committing to a
full plan before acting is not a handicap. It is the same reason a
shortest-path solver does not need to re-observe the board after every
step either.

## The environment

`core/gridworld.py` is a 5x5 board (`sample_grid`, rejection-sampled via BFS
so every generated board is solvable — an unreachable goal would silently
deflate every policy's success rate for a reason that has nothing to do with
policy quality). One start cell, one goal cell, 4 wall cells. An agent that
tries to move off the board or into a wall simply stays put; that is the
environment's own defined answer for an illegal move, not a special case the
caller has to guard against.

## The two baselines mission.yaml requires

**Random** — a uniform-random string over `U`/`D`/`L`/`R`, the floor.

**Greedy one-step lookahead** — at each simulated step, take whichever
action reduces Manhattan distance to the goal the most, breaking ties by a
fixed order. This is a real heuristic with a real, discoverable failure
mode: it has no memory of visited cells, so a wall layout that requires
temporarily moving *away* from the goal to route around an obstacle traps it
oscillating for the rest of the step budget. That is why it is beatable, not
a bug — `mission.yaml` asks for exactly this kind of baseline, not an
optimal solver.

The greedy baseline is a one-step lookahead with no memory: at each position
it evaluates all 4 actions in fixed order `U, D, L, R`, computes Manhattan
distance to the goal after each candidate, and takes the first action
achieving the strict minimum. This is pure greedy descent on distance with no
lookahead beyond one move -- if the only path to the goal requires a move
that *increases* distance (routing around a wall segment), greedy never
takes it, because every candidate it considers only in terms of immediate
distance reduction. Measured over 500 real trials, this baseline still
reaches the goal 82.4% of the time (`mean_steps_on_success = 3.15`) -- the
trap triggers on a minority of sampled boards, not the common case, which is
exactly what makes it a real bar rather than a strawman.

<!-- interactive: GreedyLookaheadTrap -->

Manhattan-distance greedy descent is the textbook baseline against A* search
(Hart, Nilsson & Raphael, 1968), which fixes exactly this trap by using the
same heuristic as a lower bound inside best-first search with backtracking,
rather than as the entire policy.

```
 random: 111/500 = 0.222  mean_steps_on_success=5.43
 greedy: 412/500 = 0.824  mean_steps_on_success=3.15
```

Neither number is degenerate (0% or 100%) — the property this stage actually
needs before stage 01 spends any training compute. A saturated greedy
baseline would leave no room to beat it; a near-zero one would say more
about task difficulty than about any policy. Full numbers in
[`runs/2026-07-31-baselines.md`](runs/2026-07-31-baselines.md).

## Run it

```bash
cd 05-game-ai/00-gridworld-baselines/core
uv run python measure_baselines.py --trials 500
```

Pure Python, no dependencies — not torch, not gymnasium. Both baselines and
the environment are deterministic given a seed; 500 grids x 2 policies runs
in 0.02s.

## What this stage does not establish

Whether a cold-start GRPO policy — a randomly initialized Transformer, the
same starting point mission 01's own arithmetic RL run used — ever escapes
degenerate rollout groups on this environment at all. That is stage 01's
open question, not a formality: mission 01's own arithmetic policy never
escaped it at 200 steps, which is exactly the wall this mission exists to
check for on a different reward source.

## The fix and its trade

The fix this stage exists to build is the baseline pair itself, and the
trade is that both numbers must land between degenerate and saturated.
Random (0.222) is the no-learning floor: it proves the environment is not a
zero-sum trap where any policy scores near zero. Greedy one-step lookahead
(0.824) is the beatable bar: its no-memory wall trap (it oscillates when a
route requires temporarily moving away from the goal) is what keeps it
short of perfect, so a trained policy has a real, non-degenerate space to
earn -- 0.222 to 0.824, against a stage-01 result that later lands below
the floor entirely. A saturated greedy baseline would have left no room to
beat; a near-zero one would have said more about task difficulty than about
any policy. The cost of the check is that the greedy baseline is a
deliberately weak target -- a team that beats it has beaten a heuristic
with no memory, not a good policy -- which is exactly the honest bar
`mission.yaml` asked for before any training compute was spent.

## Who owns this loop

- **The environment owner** owns the solvability guarantee: boards are
  rejection-sampled via BFS so every generated grid is solvable, and an
  unreachable goal would silently deflate every downstream success rate
  for a reason unrelated to policy quality.
- **The baseline owner** owns the two-reference contract and its
  non-degeneracy rule (neither baseline may be near 0% or 100%), because
  stage 01's verdict and stage 02's report both inherit these numbers.
- **The evaluation owner** owns the greedy heuristic's documented trap:
  the wall-oscillation behavior is a discoverable, stated failure mode,
  not a hidden bug -- it is the reason the baseline is beatable and must
  stay visible for the comparison to be fair.

**Next:** stage 01 imports mission 01's GRPO mechanism unmodified and trains
a policy against this environment's terminal reward.

A detour from here: [why the no-learning floor is not near
zero](when-random-gets-22-percent/) — the recorded baselines read: random
solves 22.2% (5.43 mean steps) and greedy one-step solves 82.4% (3.15),
so a trained policy has a real, non-degenerate space to earn.

Another detour: [the 82.4% ceiling of one-step lookahead](when-greedy-is-not-perfect/) — the recorded baselines read: greedy can commit to a dead end the step it enters, so 82.4% is the horizon's ceiling, and the random-to-greedy gap is the bar a trained policy must clear.
