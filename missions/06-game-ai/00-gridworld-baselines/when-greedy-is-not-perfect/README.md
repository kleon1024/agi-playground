---
status: verified
level: applied
base: scratch
label: When greedy is not perfect
verified: 2026-08-06
---

# The 82.4% ceiling of one-step lookahead

**Question:** [stage 00's baselines](../) measured greedy one-step
lookahead at 82.4%. This chapter reads the recorded run and asks why a
policy with a plan is not perfect.

**Before this:** [stage 00's grid-world baselines](../) and its recorded
JSON.

## The baseline, read

The run ([record](runs/2026-08-06-greedy-read.md)) reads the recorded
numbers:

| baseline | solved | mean steps on success |
|---|---:|---:|
| random | 111/500 (0.222) | 5.43 |
| greedy one-step | 412/500 (0.824) | 3.15 |

Board: 5x5, 4 walls, max_steps 12.

## Two readings

**One-step lookahead can commit to a dead end the step it enters.** Greedy
moves toward the goal if the immediate cell is open — it cannot see around
the corner, so it can step into a dead end and waste its remaining budget
there. That is the mechanism behind 82.4%, not 100%: the ceiling is the
policy's horizon, not the environment's difficulty.

**The gap between random and greedy is the space a trained policy would
have to earn.** Random solves 0.222 in 5.43 steps; greedy solves 0.824 in
3.15 — the two baselines bracket the honest bar. A trained policy must
clear the greedy number to beat a cheap heuristic, and the recorded gap
(0.222 -> 0.824) is what makes "beats the baseline" a meaningful claim.

## Evidence boundary

The committed baselines JSON (500 trials per baseline, one board size, one
wall count). It reads that artifact; it does not re-run the trials.

## Check your mental model

Answer each before opening it.

**1. Why is greedy not a shortest-path solver?**

<details>
<summary>Answer</summary>

Because it looks one step ahead, not to the goal. A shortest-path solver
plans the whole route before moving; greedy commits to the first open
cell toward the goal and discovers too late that the path dead-ends. The
82.4% is the fraction of boards where one-step lookahead happens to work
— the rest need the horizon greedy lacks.

</details>

**2. What does mean-steps-on-success add to the solve rate?**

<details>
<summary>Answer</summary>

It prices efficiency. Greedy not only solves more boards, it solves them
in fewer steps (3.15 vs 5.43) — so the baseline is dominant on both axes,
not a tradeoff. A trained policy that matches 82.4% but needs more steps
would not actually be better, and reporting both numbers is what makes
"beats the baseline" a complete claim.

</details>

## Next

Back to [stage 00](../), or to
[why the no-learning floor is not near zero](../when-random-gets-22-percent/)
which reads the same JSON's random side.
