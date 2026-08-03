---
status: verified
level: applied
base: scratch
verified: 2026-07-31
label: GRPO against the grid-world
---

# Does GRPO produce a policy that beats the baselines it must clear?

**Question:** stage 00 measured two real baselines on this grid-world --
random (22.2%) and a greedy one-step heuristic (82.4%) -- neither degenerate,
so a trained policy has real room to move either direction. This stage trains
a cold-start policy with GRPO, imported unmodified from mission 01's own
arithmetic RL run, and measures where it actually lands.

**The artifact this stage produces** is the same greedy-decoded completion on
every held-out board, for all 3 trained seeds:

```
seed 0: 'RRRRRRRRRRRR'  on all 8 sampled held-out boards
seed 1: 'UUUUUUUUUUUU'  on all 8 sampled held-out boards
seed 2: 'LLLLLLLLLLLL'  on all 8 sampled held-out boards
```

**Before this:** [stage 00](../00-gridworld-baselines/) built the environment
and measured both baselines this stage compares against.

## What did not change from mission 01's arithmetic run

`core/train_grpo.py` imports `rollout_group`, `Rollout`, `Transformer`,
`Config`, and `grpo_loss` directly from
[mission 01 stage 04-rl's `grpo.py`](../../01-language-model-agent/04-rl/core/grpo.py)
-- the group-relative advantage, clipped surrogate, and KL leash against a
frozen reference are the exact same code, not a reimplementation. What
changed is only the reward function (`core/reward.py`'s
`compute_reward` -- legal-move format credit plus a terminal
goal-reached bit, in place of arithmetic's string match) and the rollout
environment (`core/env_text.py` renders a board as a text prompt; the
sampled completion is decoded back into a `U`/`D`/`L`/`R` action string and
replayed against [stage 00's `gridworld.py`](../00-gridworld-baselines/core/gridworld.py)
to score it).

The one non-obvious piece of plumbing: `env_text.py` builds its vocabulary
the same way `grpo.py` builds its own -- specials first (`<pad>`, `<eos>`),
then the rest sorted -- which places `PAD_ID` and `EOS_ID` at the same two
positions (0 and 1) in both vocabularies. That is the entire reason
`rollout_group` and `grpo_loss` -- which reference `PAD_ID`/`EOS_ID` as bare
module globals, not parameters -- run against a completely different
character set with no patching at all.

The policy itself is the same `Transformer` class as mission 01's pretraining
run, imported unmodified, instantiated with a much smaller config for this
task's 28-character vocabulary:
`Config(vocab_size=28, n_layer=4, n_head=4, n_kv_head=2, d_model=128,
d_ff=320, block_size=96)` -- 692,864 parameters total.

<!-- interactive: ModelArchitecturePolicy -->

## What ran

3 independent seeds, 200 GRPO steps each, 4 sampled grid problems per step,
group size 8, 2 inner epochs, against the same 5x5/4-wall/12-step-budget
environment stage 00 measured. Wall-clock 118-131s per seed, CPU only.
Degenerate steps (every rollout in a step scored identically, contributing
zero gradient): 0, 0, and 1 out of 200 -- unlike mission 01's own arithmetic
run, this environment's reward source did not make degenerate groups the
dominant outcome.

Two decode modes were evaluated afterward, both on 500 fresh held-out grids:
**greedy** (argmax, what a deployed policy would run) and **sampled**
(temperature 1.0, the same distribution training's own rollouts are drawn
from).

## Result

```
                    eval (greedy)   eval (sampled, T=1.0)   train-time peak mean_success
 seed 0:  39/500 = 0.078          91/500 = 0.182          0.417 (step 55)
 seed 1:  31/500 = 0.062          72/500 = 0.144          0.500 (step 20)
 seed 2:  39/500 = 0.078         105/500 = 0.210          0.406 (step 115)
```

Both baselines from stage 00, for comparison: random = 0.222, greedy
heuristic = 0.824.

**Greedy-decode eval, the way a deployed policy would actually run, is worse
than the random baseline on all 3 seeds** -- 6.2-7.8% against 22.2%. Sampled
decode does better (14.4-21.0%) but still does not clear random on any seed.
Training-time success (sampled, logged every 5 steps) reached 40-50% at
various points without ever stabilizing there, falling back to 6-31% by the
final logged step.

## Why: greedy decode collapsed to one constant, board-independent action

Dumping the greedy completion on 8 different held-out boards per seed shows
the exact same string every time, regardless of the board:

```
 seed 0: always 'RRRRRRRRRRRR'
 seed 1: always 'UUUUUUUUUUUU'
 seed 2: always 'LLLLLLLLLLLL'
```

Each seed's argmax policy locked onto a single repeated action -- a
different one per seed -- and ignores the board in the prompt entirely. The
reported greedy success rates are exactly the real hit rate of "always move
right" (or up, or left) against 500 random grids: it wins when the goal
happens to sit in that fixed direction from start, and otherwise fails,
which is a lower bar than exploring four directions randomly clears. Format
reward stayed high throughout training for all 3 seeds (the policy reliably
learned to emit legal `U`/`D`/`L`/`R` characters) -- what did not stick was
conditioning *which* character on the actual board. Sampling scores higher
than greedy for exactly this reason: it draws from the rest of the logit
distribution instead of only the top-1 token, so it occasionally emits the
board-appropriate action even though the model's single most confident
choice per position has not learned to depend on the board.

Greedy decode takes argmax over the policy's output distribution at each
position; sampled decode (T=1.0) draws from that same distribution
proportionally. The two only diverge sharply when the distribution has a
narrow but not overwhelming peak -- if training pushed most probability mass
for the first action onto one direction but left a real, board-correlated
tail too small to win argmax but large enough to sometimes win a draw,
greedy reads as "always the same action" while sampled reads as "usually
that action, but board-appropriate directions come through often enough to
move the aggregate." The per-seed numbers match: sampled decode
(14.4-21.0%) is 2.3-2.7x greedy decode (6.2-7.8%) on every seed, larger than
temperature alone would produce from a policy whose distribution is
genuinely board-independent.

<!-- interactive: DecodeModeCollapse -->

This greedy-vs-sample divergence after RL training is a documented failure
mode in RLHF literature under the name "mode collapse" -- usually discussed
for language generation diversity, which makes this grid-world result a
small, mechanistically legible instance of a pattern usually only observed
at LLM scale.

Full training curves, per-seed detail, and the concrete example dump are in
[`runs/2026-07-31-grpo-training.md`](runs/2026-07-31-grpo-training.md).

## What this stage establishes

A real, reproducible, mechanistically-explained result, not a degenerate
one: GRPO on this grid-world produces real gradient signal (199-200 of 200
steps per seed contributed a non-zero-variance group) and a policy that
clearly learns *something* -- legal-move formatting, and enough board
sensitivity for sampled decode to land at 14-21% -- but the argmax policy it
converges to does not make its move choice depend on the board, on any of 3
seeds, at this scale (200 steps, group size 8, a 4-layer from-scratch
Transformer with no pretraining). This is a different shape of finding than
mission 01's own arithmetic null result, which never escaped degenerate
rollout groups at all; here training clearly moved, and still did not arrive
at a board-conditional policy.

## What this stage does not establish

Whether more steps, more rollouts per group, a larger model, or a different
KL budget would let board-conditioning stick under greedy decode -- none of
those were varied here. Whether this specific failure mode (format learned,
board-conditioning not) is particular to this reward shape (dense per-format
credit, sparse per-episode success credit) or would recur with a different
one. Whether this result beats or loses to either baseline in mission.yaml's
own formal sense -- that mechanical comparison against the declared
acceptance bar is stage 02's job, not this stage's.

**Next:** stage 02 applies mission 06's acceptance bar to these per-seed
results against both stage 00 baselines and reports MET, NOT MET, or an
honest null result.
