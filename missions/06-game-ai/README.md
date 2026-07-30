---
status: draft
level: applied
label: Game AI
---

# Does RL sharpen a policy that already wins sometimes, or does nothing happen?

**Question:** you have a policy that plays a simple game and wins some of
the time — by luck, by a heuristic, by a small amount of prior training. Is
it worth applying reinforcement learning to make it win more, or is that a
wasted afternoon on a policy too weak for RL to move at all?

**The artifact this mission follows** is one training run: a policy, an
environment with a verifiable win/score condition, and a reward curve that
either climbs or — just as informative — never leaves zero.

## Why this mission exists

[Mission 01's stage 04-rl](../01-language-model-agent/04-rl/) built GRPO from
scratch against an arithmetic task and got a real null result: every one of
200 training steps came back with every rollout in its group scoring
identically, so the group-normalized advantage was `0/0` for the entire run
and not a single optimizer step was taken. The policy was too weak, at that
scale, to ever stumble into a well-formed completion — RL had nothing to
sharpen.

That result drew a boundary sharper than "RL is powerful": **GRPO sharpens
behavior a policy already produces sometimes; it cannot install behavior
that is absent.** A game's win condition is a verifiable reward exactly like
arithmetic correctness — computed by a rule, not a learned model — so this
mission asks the same question of a different reward source, using the
identical training loop: does *this* starting policy, on *this* game, clear
the bar mission 01's arithmetic policy did not?

## What gets measured

Two baselines the same way mission 04 uses two baselines — because a single
number invites picking whichever baseline flatters it.

**Random policy** — uniform-random legal actions. The floor, not a serious
comparison.

**Scripted/heuristic policy** — a simple hand-written rule for the chosen
environment. This is the baseline that actually matters: it is cheap, it is
often already decent, and a stakeholder deciding whether RL is worth the
compute is really asking whether it beats *this*, not whether it beats
random play.

**Success/win rate** on the environment's own terminal signal is the metric,
reported beside both baselines and total training compute, across at least
3 seeds — RL training is non-deterministic, the same discipline
[mission 01's task suite](../01-language-model-agent/07-eval/) and
[the architecture ablation ladder](../../platform/training/02-architecture-ablations/)
already apply: a gap smaller than the run-to-run spread is reported as no
result.

## The training loop is imported, not rebuilt

This mission's core training code imports GRPO directly from
[`../01-language-model-agent/04-rl/core/grpo.py`](../01-language-model-agent/04-rl/core/grpo.py)
— the rollout sampler, the group-normalized advantage, the clipped surrogate,
and the KL leash against a frozen reference are unmodified. What changes is
the rollout environment (an episode in a game, not a single text completion)
and the reward function (the environment's terminal score, not string-matched
arithmetic correctness). This is the repo's own cross-mission convention:
missions reuse each other's `core/` directly via import rather than
duplicating the mechanism, the same way mission 04's agent harness reuses
[`capabilities/act-coordinate`](../../capabilities/act-coordinate/) rather
than rewriting a tool loop.

## The wall this mission is watching for

Mission 01's null result came from a cold-start policy against a
low-probability target shape — a randomly initialized few-hundred-thousand-
parameter model almost never emits `<think>...</think><answer>...</answer>`
by chance, so every group came back degenerate. A game has an analogous
failure mode: a cold-start policy on a hard environment can fail (or
succeed) identically across an entire rollout group, for the same reason —
not enough prior competence for the reward to discriminate between samples.
Choosing an environment and starting policy where this mission's rollouts
*aren't* uniformly degenerate is itself part of the job, and if they are,
that is reported exactly the way mission 01 reported its own zero-gradient
run — as a real finding, not a bug to quietly fix by rescaling after the
fact.

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — Task and environment](00-gridworld-baselines/) | what counts as a verifiable reward in a game, and does the starting policy clear the bar RL needs? | verified |
| [01 — GRPO loop](01-grpo/) | does group-relative RL move the success rate at all, or hit the same zero-gradient wall mission 01 did? | verified |
| [02 — Report](02-report/) | baselines, seeds, compute, and an honest verdict | verified — NOT MET |

[Stage 00](00-gridworld-baselines/) built a 5x5 grid-world (deterministic,
BFS-checked solvable, no dependencies) and measured both required baselines
over 500 real episodes: random reaches the goal 22.2% of the time, greedy
one-step lookahead 82.4% — a real, non-degenerate gap, since a saturated or
near-zero baseline would leave stage 01's training run nothing to say. Full
numbers in [its run record](00-gridworld-baselines/runs/2026-07-31-baselines.md).

[Stage 01](01-grpo/) trained 3 seeds with GRPO imported unmodified from
mission 01's arithmetic run, substituting only the reward function and
rollout environment. Unlike mission 01's own cold-start run, this policy did
not get stuck in degenerate rollout groups — 199-200 of 200 steps per seed
took a real gradient step, and training-time success reached 40-50% at
points. But the argmax policy every seed converged to ignores the board
entirely, always emitting one constant repeated action (`RRRRRRRRRRRR`,
`UUUUUUUUUUUU`, or `LLLLLLLLLLLL` depending on the seed) regardless of the
prompt — greedy-decode eval (6.2-7.8%) lands below the random baseline
(22.2%) on all 3 seeds, and sampled-decode eval (14.4-21.0%) does better but
still doesn't clear random. Full mechanism and per-seed numbers in
[its run record](01-grpo/runs/2026-07-31-grpo-training.md).

[Stage 02](02-report/) held stage 01's result against this mission's own
acceptance bar and printed `NOT MET` — not because training failed to move
(199-200/200 steps per seed took a real gradient step, unlike mission 01's
zero-gradient run) but because the policy it converged to decisively loses to
both baselines under greedy decode, the decode mode a deployed system would
actually use. Escaping degenerate rollout groups turned out to be necessary
for GRPO to move a policy here, but not sufficient for the result to be a
useful, board-conditional one. Full verdict and failure catalogue in
[its run record](02-report/runs/2026-07-31-outcome-report.md).

Per [the mission contract](../../standards/mission-contract.md), this
contract is declared before any stage is built, so the environment and
baseline cannot be chosen after seeing which ones flatter a result.

## What this will not prove

Nothing about complex, real-time, partially-observed, multi-agent, or
pixel-observation games — the environments here are small, fully observed,
and sized to train in minutes. A result here says nothing about a harder
game, and nothing about combining this mission's RL loop with a perception
stage (that dependency runs the other way: perception would need
[mission 05](../05-vision-language-model/)'s work, not this mission's). Full
boundary in [`mission.yaml`](mission.yaml) under `does_not_prove`.
