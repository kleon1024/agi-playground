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
[the architecture ablation ladder](../../missions/01-language-model-agent/02-pretrain/architecture-ablations/)
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
[mission 01's agent harness](../01-language-model-agent/06-agent/) rather
than rewriting a tool loop.

GRPO's one departure from PPO is how it computes the advantage `A_i` for each
of the `G` completions sampled per prompt. PPO trains a value network
`V(s)` and sets `A(s,a) = Q(s,a) - V(s)`. GRPO trains no value network:
`A_i = (r_i - mean(r_1..r_G)) / (std(r_1..r_G) + eps)`. If every completion
in a group scores identically, `std = 0`, `A_i` becomes `0/0` for every
member, and the group contributes no gradient. Mission 01's arithmetic run
hit this wall on all 200 of 200 steps -- a randomly initialized policy
essentially never emitted a well-formed completion, so every group's rewards
were identical and the run never took an optimizer step. Stage 01's
grid-world run does not: only 1 of 200 steps per seed came back degenerate
(`degenerate_steps: [0, 0, 1]` across seeds), because legal-move format
credit plus a terminal goal bit gives the policy enough surface area to
produce variance within almost every group.

The advantage arithmetic behind that degeneracy is derived, and made
drivable, in [mission 01's RL stage](/playground/missions/01-language-model-agent/04-rl#the-group-relative-trick).

Group Relative Policy Optimization was introduced by Shao et al. in the
DeepSeekMath paper (2024) to drop PPO's value network for LLM RL
fine-tuning; it became widely known a year later as the RL algorithm behind
DeepSeek-R1 (2025).

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

## Model lineage

The GRPO loop is a point on the policy-RL line — DQN, PPO, GRPO, RLVR. The
[open-source line behind game AI](../../reference/research/lineages/06-game-ai.md)
traces it, including where the cold-start wall came from.

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — Task and environment](00-gridworld-baselines/) | what counts as a verifiable reward in a game, and does the starting policy clear the bar RL needs? | verified |
| [01 — GRPO loop](01-grpo/) | does group-relative RL move the success rate at all, or hit the same zero-gradient wall mission 01 did? | verified |
| [02 — Report](02-report/) | baselines, seeds, compute, and an honest verdict | verified — NOT MET (grid-world scope alone) |
| [03 — Fixing the collapse](03-fixing-collapse/) | is stage 01's greedy-decode collapse fixable via group size or an entropy bonus, on the same grid-world? | verified — neither fix worked |
| [04 — MiniGrid](04-minigrid/) | does a real partially-observed environment change the outcome? | verified — cold-start null result, 0 gradient steps taken |
| [05 — Full-chain report](05-report/) | baselines, seeds, compute, and an honest verdict across the mission's full approved scope | verified — MET, as an honest null result |
| [06 — Tool-use decision](06-tool-use-rl/) | does the same GRPO loop learn *when* to pay for a tool, not just what to say? | verified — 1/3 seeds calibrated, 2/3 collapsed |

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

[Stage 03](03-fixing-collapse/) tested whether stage 01's collapse is
fixable by tuning the training signal alone, on the identical 5x5
grid-world: smaller rollout groups (per Fan et al., "Learning Without
Critics? Revisiting GRPO in Classical RL Environments," 2025, which found
smaller groups reduced collapse in classical-RL settings) and a direct
entropy bonus. Neither fixed it — smaller groups made every measured number
worse across all 3 seeds tested, and the entropy bonus raised mid-training
entropy without changing which action wins the argmax. Full numbers in
[its run record](03-fixing-collapse/runs/2026-08-01-collapse-fix-sweep.md).

[Stage 04](04-minigrid/) moved to MiniGrid, a genuinely partially-observed
environment (a 7x7 egocentric patch, not the whole board), with a new
interleaved rollout loop and a custom `masked_grpo_loss` to handle
non-contiguous action-token positions. Confirmed the room solvable first (a
wall-following heuristic reaches 100% success; random reaches only 0.4%).
Training then hit a harder wall than stage 01's: every rollout group across
all 3 seeds drew identical (zero) reward, so not one gradient step was ever
taken — the same "GRPO cannot install absent behavior" boundary mission 01
found, recurring because the cold-start policy's success rate never cleared
the threshold a group needs to see any reward variance at all. Full numbers
in [its run record](04-minigrid/runs/2026-08-01-minigrid-cold-start.md).

[Stage 05](05-report/) held the full chain — stages 00-01, 03, and 04 —
against this mission's acceptance bar and printed `MET, as an honest null
result`: stage 01's collapse resisted the two most direct fixes tried in
stage 03, and stage 04 found a second, mechanistically-explained null
result in a harder domain. Full verdict in
[its run record](05-report/runs/2026-08-01-full-chain-report.md).

[Stage 06](06-tool-use-rl/) extends the same GRPO machinery to a new decision
variable beyond the original grid-world/MiniGrid scope: whether to answer an
arithmetic problem directly, at a simulated accuracy that degrades with
digit count, or pay a fixed penalty to invoke a calculator tool that is
always correct. `mission.yaml`'s `does_not_prove` field was extended, not
rewritten, to name this stage's own synthetic, single-tool, single-step
scope boundary before it was built. Its 3-seed result is the mission's first
that is not a uniform null: one seed's greedy policy matches the
calibrated-oracle decision at all 5 difficulty levels exactly, while the
other two collapse to the same context-independent behavior stages 01 and
04 already documented -- a real, seed-dependent split, not a clean win.
Full numbers in [its run record](06-tool-use-rl/runs/2026-08-03-grpo-training.md).

Per [the mission contract](../../reference/standards/mission-contract.md), this
contract is declared before any stage is built, so the environment and
baseline cannot be chosen after seeing which ones flatter a result.


## Where each stage leaves the path

A stage states a decision; these deep-dive chapters answer the decisions
the main path asserts without showing, mission-01 style — each returns an
artifact or a measurement the next stage consumes.

| At this stage | You need to decide | So read |
|---|---|---|
| `00-gridworld-baselines` | Why the no-learning floor is not near zero | [when-random-gets-22-percent](00-gridworld-baselines/when-random-gets-22-percent/) |
| `01-grpo` | The same decoder, a reward that rewards the wrong thing | [the-policy-anatomy](01-grpo/the-policy-anatomy/) |
| `01-grpo` | The policy that learned one direction | [when-the-policy-collapses](01-grpo/when-the-policy-collapses/) |
| `02-report` | The honest NOT MET: how the verdict is built | [when-the-verdict-is-not-met](02-report/when-the-verdict-is-not-met/) |
| `03-fixing-collapse` | The one direction the collapse sweep never tried | [the-diversity-direction](03-fixing-collapse/the-diversity-direction/) |
| `04-minigrid` | Why is the cold start total on MiniGrid? | [when-the-cold-start-is-total](04-minigrid/when-the-cold-start-is-total/) |
| `05-report` | The honest null, elevated to a verdict | [when-the-null-is-elevated](05-report/when-the-null-is-elevated/) |
| `06-tool-use-rl` | Why did two seeds stop paying for the tool? | [when-two-seeds-stopped-paying](06-tool-use-rl/when-two-seeds-stopped-paying/) |


## What this will not prove

Stages 00-02 (fully observed, short-horizon grid-world) prove nothing about
complex, real-time, or partially-observed games. Stage 04's MiniGrid
extension is a real partially-observed environment (compact 7x7x3
observation, sparse terminal reward), but it still proves nothing about
pixel observations, real-time play, multi-agent or competitive play, or
environments without early termination — per Fan et al. (2025), GRPO's
group-relative advantage is known to degrade without episode boundaries,
and MiniGrid's goal/lava termination keeps this mission inside that
known-viable regime deliberately. A result here does not generalize to game
engines or continuous-control games, and does not require [mission
05](../05-vision-language-model/)'s vision work, since MiniGrid's
observation is a compact symbolic grid, not pixels. Full boundary in
[`mission.yaml`](mission.yaml) under `does_not_prove`.
