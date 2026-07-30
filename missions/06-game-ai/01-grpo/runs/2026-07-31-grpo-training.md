# GRPO training against the grid-world, 3 seeds

## Command

```bash
cd missions/06-game-ai/01-grpo/core
uv run --group torch python train_grpo.py --steps 200 --group-size 8 --prompts-per-step 4 --eval-trials 500 --seed 0
uv run --group torch python train_grpo.py --steps 200 --group-size 8 --prompts-per-step 4 --eval-trials 500 --seed 1
uv run --group torch python train_grpo.py --steps 200 --group-size 8 --prompts-per-step 4 --eval-trials 500 --seed 2
```

Apple silicon laptop, macOS 15.6.1, CPU only (`--device cpu`, default). Repository
HEAD at time of run: `6928025`. 4-layer, 4-head (2 KV heads), `d_model=128`
Transformer -- the same architecture shape mission 01's own `04-rl` arithmetic
run uses, imported unmodified from
[`grpo.py`](../../01-language-model-agent/04-rl/core/grpo.py). Wall-clock:
130.8s / 118.1s / 123.9s for seeds 0/1/2 (200 steps each, training loop only,
not counting eval).

## What ran

Each seed: 200 GRPO steps, 4 sampled grid problems per step, group size 8
(8 rollouts per problem), 2 inner epochs per step, clip-eps 0.2, KL-beta 0.04,
temperature 1.0, against the same 5x5/4-wall/12-step-budget environment stage
00 measured its baselines on. Degenerate steps (every rollout group in a step
scored identically, contributing zero gradient): seed 0 = 0, seed 1 = 0,
seed 2 = 1, out of 200 -- unlike mission 01's own arithmetic run, this
environment did not collapse into degenerate rollouts as its dominant failure
mode.

Two decode modes were evaluated after training, both on 500 fresh grids
(`seed + 10_000`, disjoint from every grid seen during training):

- **Greedy** -- argmax decode, the way a deployed policy would actually run.
- **Sampled** -- temperature-1.0 decode, the same distribution training's own
  rollouts are drawn from.

8 concrete greedy-decoded examples per seed were also dumped
(`seed + 20_000`, a third disjoint grid stream).

## Result

```
                    eval (greedy)   eval (sampled, T=1.0)   train-time peak mean_success
 seed 0:  39/500 = 0.078          91/500 = 0.182          0.417 (step 55)
 seed 1:  31/500 = 0.062          72/500 = 0.144          0.500 (step 20)
 seed 2:  39/500 = 0.078         105/500 = 0.210          0.406 (step 115)
```

Compare against stage 00's baselines: random = 0.222, greedy heuristic = 0.824.

**GRPO's greedy-decode eval (6.2-7.8%) is worse than the random baseline
(22.2%), on all 3 seeds, by a wide margin.** Sampled-decode eval (14.4-21.0%)
is closer to random but still below it on all 3 seeds. Training-time
temperature-sampled success climbed as high as 41.7-50.0% at various points
during training without ever stabilizing there -- by the final logged step
(195) it had fallen back to 6.2-31.2%.

## Why: greedy decode collapsed to one constant, board-independent action

Dumping the greedy completion on 8 different held-out boards per seed shows
literally the same string on every board:

```
 seed 0: 'RRRRRRRRRRRR' on all 8 examples
 seed 1: 'UUUUUUUUUUUU' on all 8 examples
 seed 2: 'LLLLLLLLLLLL' on all 8 examples
```

Each seed's argmax policy locked onto a single repeated action -- a different
one per seed, matching whichever direction that seed's own training
trajectory happened to reinforce hardest -- and emits it regardless of the
board in the prompt. The reported greedy success rates (7.8%/6.2%/7.8%) are
exactly the real-world hit rate of "always move right" / "always move up" /
"always move left" against 500 random grids: this policy sometimes reaches
the goal by coincidence (a goal that happens to sit in that fixed direction
from start) and otherwise fails, which is a lower bar than a random walk of
four different directions clears.

Sampling scores higher than greedy precisely because it draws from the rest
of the logit distribution instead of only the single most-probable token, so
it occasionally emits the board-appropriate action even though the model's
top-1 choice per position has not learned to depend on the board. Format
reward (`mean_format`, logged in `history`, typically 0.6-0.85 by the later
steps) was high throughout for all 3 seeds -- the policy reliably learned to
emit legal `U`/`D`/`L`/`R` characters -- but the additional, harder signal of
conditioning *which* character on the actual board layout did not stick.

## What this run establishes

A real, reproducible, mechanistically-explained failure: GRPO training on
this grid-world, at this scale (200 steps, group size 8, 4 prompts/step, a
4-layer from-scratch Transformer with no pretraining), does not produce a
policy that beats even the random baseline at eval time, on any of 3 seeds,
despite producing real training-time reward signal along the way (non-zero
gradients on 199-200/200 steps, temperature-sampled success reaching 40-50%
at points during training). This is not the same finding as mission 01's own
arithmetic null result (which never escaped degenerate rollout groups at
all) -- here the model clearly learns *something* (legal-move formatting,
and enough board sensitivity for sampled decode to land at 14-21%), but the
argmax policy it converges to has not learned to make its move choice
actually depend on the board, which is the one thing this task requires.

## What this run does not establish

Whether more steps, a larger model, more rollouts per step, or a lower KL
budget would let conditioning on the board stick under greedy decode -- none
of those were varied here. Whether this failure mode is specific to this
grid-world's reward shape (dense per-format credit, sparse per-episode
success credit) or would recur with a different reward design. Nothing about
GPU-scale training; this ran on CPU, matching stage 00's environment, since
the model and data here are small enough that CPU wall-clock (~2 minutes per
seed) was the honest, sufficient choice.
