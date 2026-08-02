# GRPO training against the tool-use decision task, 3 seeds

## Command

```bash
cd missions/06-game-ai/06-tool-use-rl/core
uv run --group torch python train_grpo.py --steps 200 --group-size 8 --prompts-per-step 4 --eval-trials 1000 --seed 0 --out ../runs/grpo-seed0.json
uv run --group torch python train_grpo.py --steps 200 --group-size 8 --prompts-per-step 4 --eval-trials 1000 --seed 1 --out ../runs/grpo-seed1.json
uv run --group torch python train_grpo.py --steps 200 --group-size 8 --prompts-per-step 4 --eval-trials 1000 --seed 2 --out ../runs/grpo-seed2.json
```

Apple silicon laptop, macOS 24.6.0, CPU only (`--device cpu`, default).
Repository HEAD at time of run: `d48fe02`. Same 4-layer, 4-head (2 KV
heads), `d_model=128` Transformer every prior stage in this mission uses,
imported unmodified from
[`grpo.py`](../../../01-language-model-agent/04-rl/core/grpo.py). Same
`group_size=8`, `prompts_per_step=4`, `clip_eps=0.2`, `kl_beta=0.04`,
`inner_epochs=2`, `steps=200` as stage 01's grid-world run -- held fixed
deliberately, since this stage's only declared change is the environment
and reward, not the training budget. Wall-clock (training + 1000-trial x
2-decode-mode eval + example dump): 138.8s / 139.7s / 144.8s for seeds
0/1/2 -- all three orders of magnitude under the mission's 30-minute-per-seed
ceiling.

## What ran

Each seed: 200 GRPO steps, 4 sampled problems per step (uniform over the 5
digit-count levels), group size 8, 2 inner epochs, temperature 1.0. Every
group's reward comes from `reward.py`'s `compute_reward` -- format credit
for emitting a legal `A`/`T` character, outcome credit from either a fresh
`simulated_accuracy(digit_count)` Bernoulli draw (`ANSWER`) or the flat
`1 - TOOL_COST = 0.70` (`TOOL`). Degenerate steps (every rollout in a
step's groups scored identically): seed 0 = 1/200, seeds 1-2 = 0/200 --
consistent with stage 01's own grid-world run, and confirming the fix
described in the README (`A`/`T` single-character actions, not the spelled
words) worked: unlike this stage's first, word-based attempt, in which
**all 200/200 steps were degenerate and zero gradient steps were taken**
(not recorded as a numbered run since it never produced a trained policy;
see the README's "A design mistake worth keeping visible" section).

Two decode modes were evaluated after training, both on 1,000 fresh
problems per seed (`seed + 10_000`, disjoint from every problem seen during
training), broken down by digit-count level:

- **Greedy** -- argmax decode, the mode a deployed policy would run.
- **Sampled** -- temperature-1.0 decode, training's own rollout distribution.

## Result

```
                    eval (greedy)        eval (sampled, T=1.0)   degenerate steps
 seed 0:  mean_reward=0.8838         mean_reward=0.8456          1/200
 seed 1:  mean_reward=0.7430         mean_reward=0.7416          0/200
 seed 2:  mean_reward=0.7590         mean_reward=0.7428          0/200

 mean (3 seeds): greedy=0.7953  sampled=0.7767
 spread (3 seeds): greedy=0.1408  sampled=0.1040
```

Fixed baselines (from `runs/2026-08-03-baselines.md`): `never_tool` = 0.8654,
`always_tool` = 0.9000.

```
greedy mean vs never_tool:  0.7953 - 0.8654 = -0.0701 -> |margin| < spread (0.1408) -> within the noise band
greedy mean vs always_tool: 0.7953 - 0.9000 = -0.1047 -> |margin| < spread (0.1408) -> within the noise band
```

Neither baseline is decisively beaten or decisively lost to on the
3-seed mean, using the same margin-vs-spread rule stage 02's `report.py`
applies (a margin only counts as real if it exceeds the measured
run-to-run spread). That is not because the result is flat -- it is
because the 3 seeds are not doing the same thing.

## Per-level breakdown: one seed found the exact calibrated policy, two did not

```
                 level 1   level 2   level 3   level 4   level 5    (answer_rate under greedy decode)
 seed 0:           1.00      1.00      0.00      0.00      0.00
 seed 1:           1.00      1.00      1.00      1.00      1.00
 seed 2:           1.00      1.00      1.00      1.00      1.00

 oracle (optimal): ANSWER    ANSWER    TOOL      TOOL      TOOL
```

**Seed 0's greedy policy answers directly on levels 1-2 and invokes the
tool on levels 3-5 -- exactly the threshold `reward.py`'s
`simulated_accuracy` docstring places the crossing at, and exactly the
calibrated-oracle reference's own decision at every one of the 5 levels.**
Seeds 1 and 2 both collapse to answering directly at every level,
regardless of difficulty -- the same context-independent collapse stage
01 and stage 04 already documented, recurring here in a decision space of
size 2 instead of a grid or a partially-observed room.

Confirming seed 0's decision quality is not confounded by formatting: its
raw greedy reward (0.8838) sits *below* the calibrated-oracle reference
(0.9780) only because its completions are not perfectly clean single
characters (`dump_examples` shows repeated-character outputs like
`AAATTTTT` and `TTTTTTTT` rather than a lone `A` or `T` followed
immediately by `<eos>`), which caps `format_reward` at 0.5 instead of 1.0
on most trials. Recomputing seed 0's per-level reward *as if* every
completion had scored full format credit reproduces the calibrated-oracle
number almost exactly: `0.2*1.0 + {0.97, 0.82, 0.70, 0.70, 0.70}` averages
to 0.978, matching the oracle to three decimal places. Seed 0 learned the
right decision at every level; the gap to the oracle is a real but
orthogonal formatting inefficiency (never learning to stop immediately
after emitting the decision character), not a decision-quality gap.

Seeds 1 and 2's own raw greedy rewards (0.7430, 0.7590) land *below* even
the clean `never_tool` baseline (0.8654) they otherwise match in decision
pattern, for the identical formatting reason -- their completions are not
clean single characters either.

## Failure and success catalogue

```
degenerate rollout groups:                [1, 0, 0] / 200 steps per seed -- minor, all 3 seeds
context-independent decision collapse:     2/3 seeds (1, 2) -- always answers, ignores digit_count
calibrated, difficulty-conditioned policy: 1/3 seeds (0) -- matches the oracle decision at all 5 levels
non-clean completion format:               3/3 seeds -- no seed learned to stop immediately after
                                            the decision character, capping format credit below 1.0
```

## What this run establishes

That GRPO, using the identical mechanism and training budget as every
earlier stage in this mission, **can** learn a difficulty-conditioned
tool-invocation policy from a cold start on this environment -- something
no prior stage in this mission (01, 03, 04) ever observed on any seed. One
of three seeds reproduces the calibrated-oracle's decision boundary
exactly. That is a materially different outcome from mission 01's own
zero-gradient null result and from stage 04's MiniGrid null result, where
no seed ever escaped a context-independent or degenerate policy.

## What this run does not establish

That this is reliable: two of three seeds collapse to the same
context-independent decision stage 01 and stage 04 already documented,
so the mission's own acceptance bar (beat both baselines by more than the
measured spread) is not met on the 3-seed mean -- the spread itself is
large enough to swallow the apparent win. Nothing about why seed 0 escaped
the collapse and seeds 1/2 did not; no intervention (different learning
rate, KL budget, or group size) was tried to make the calibrated outcome
reproducible, the same kind of fix stage 03 explored for a different
collapse and is not repeated here. Nothing about whether the
non-clean-completion formatting inefficiency would resolve with more
training steps -- not varied here.
