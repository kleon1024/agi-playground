---
status: verified
level: applied
base: scratch
label: When random gets 22 percent
verified: 2026-08-06
---

# Why the no-learning floor is not near zero

**Question:** [stage 00](../) measured two baselines a trained policy must
clear: random solves 22.2% of boards, greedy one-step solves 82.4%. This
chapter reads the recorded numbers and asks what each baseline is actually
measuring.

**Before this:** [stage 00's grid-world and baselines](../).

## The baselines, read

The run ([record](runs/2026-08-06-baseline-read.md)) reads the committed
JSON:

| baseline | solved | rate | mean steps on success |
|---|---:|---:|---:|
| random | 111/500 | 0.222 | 5.43 |
| greedy one-step | 412/500 | 0.824 | 3.15 |

## Two readings

**Random is not near zero, and that is the point.** A mostly-open 5x5 board
with four walls rewards persistence: a random walk reaches the goal 22.2%
of the time. The no-learning floor is a real, measurable bar — a policy
that cannot beat "walk randomly for a while" has learned nothing, and a
mission that only compared a trained policy against a strawman near-zero
would have manufactured its own win.

**Greedy is the bar that actually separates trained from untrained.** One
step of lookahead — move toward the goal if the cell is open — solves 82.4%
in fewer steps. A trained policy must clear this, not the random floor,
because the mission's question is whether RL adds anything over cheap
heuristics. The 0.222-vs-0.824 gap is the honest space a trained policy
would have to earn.

## The fix and its trade

The fix is measuring the floor before training: the random baseline (22.2%)
is a no-learning control that makes "the trained policy learned nothing"
a falsifiable claim. The trade is that the floor is a floor — beating it
is the minimum, not a win. A policy that clears random by a hair has
learned something but not enough, which is exactly why stage 01's later
result (greedy 6.2-7.8%, *below* random) is read as a collapse rather than
as a near-miss: the floor is what makes "worse than nothing" visible.

## Who owns this loop

The baseline owner, with the environment owner as the gate. The baseline
owner keeps the 500-trial protocol and the fixed board construction
(5x5, 4 walls, max_steps 12) frozen so the floor is comparable across
stages; the environment owner's BFS-rejection guarantee is what keeps
22.2% a property of random behavior rather than of unsolvable boards. A
team that re-measures the floor with a different board distribution is
comparing against a different claim.

## Evidence boundary

The committed baselines JSON (500 trials per baseline, one board size, one
wall count); it reads that artifact and does not re-run the trials. It does
not claim either baseline is the best possible cheap policy, only the two
`mission.yaml` requires.

## Check your mental model

Answer each before opening it.

**1. Why does the mission report random at 22.2% instead of testing only
against greedy?**

<details>
<summary>Answer</summary>

Because the two baselines answer different questions. Random is the
no-learning floor — does the policy do better than chance persistence?
Greedy is the cheap-heuristic bar — does RL add anything over a one-step
lookahead? Mission 06's report needs both, because a policy that clears
random but not greedy has learned something without learning enough.

</details>

**2. What does mean-steps-on-success add beyond the solve rate?**

<details>
<summary>Answer</summary>

It prices efficiency. Greedy not only solves more boards, it solves them in
fewer steps (3.15 vs 5.43) — so the greedy baseline is dominant on both
axes, not a tradeoff. A trained policy would have to beat both numbers, and
reporting both is what makes "beats the baseline" a complete claim.

</details>

## Next

Back to [stage 00](../), or forward to
[stage 01 — GRPO](../../01-grpo/) which trains a policy against these two bars.
