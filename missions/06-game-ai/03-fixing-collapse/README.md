---
status: verified
level: applied
base: scratch
verified: 2026-08-01
label: Fixing the collapse
---

# Is stage 01's greedy-decode collapse fixable by tuning the training signal alone?

**Question:** stage 01 found a policy that trains (199-200/200 real
gradient steps per seed) and shows real board sensitivity under sampled
decode (14.4-21.0%), but whose greedy (argmax) policy ignores the board
entirely, on all 3 seeds. Is that collapse a property of *this specific
training signal* -- fixable by changing group size or adding an entropy
term, with the environment and reward held fixed -- or something deeper?

**The artifact this stage produces** is two real, negative sweep results
against stage 01's own baseline, on the identical 5x5 grid-world.

**Before this:** [stage 01](../01-grpo/), which supplies the environment,
vocab, reward, and GRPO mechanism this stage reuses unmodified.

## What was tried

**Smaller groups.** Fan et al., "Learning Without Critics? Revisiting GRPO
in Classical RL Environments" (2025), found that in their classical-RL
experiments, *smaller* rollout groups reduced collapse -- the opposite of
typical LLM-RLHF intuition, where bigger groups usually help. This stage
tested `group_size=4` (half of stage 01's 8) across 3 seeds.

**An entropy bonus.** The collapse is specifically an argmax phenomenon:
sampled decode already shows real board sensitivity, so the policy's full
distribution carries signal that greedy decode's argmax discards. A direct
entropy bonus (`total_loss - entropy_coef * mean_completion_entropy`,
computed locally in this stage's own train loop -- `grpo.py`'s
`grpo_loss`/`rollout_group`/`token_logprobs` are not modified) was tested at
`entropy_coef=0.01`, one seed, since raising the whole distribution's
entropy is a more direct lever on "does greedy ignore the board" than group
size is.

## What happened

| Variant | Degenerate steps / 200 (mean or single) | Greedy success | Sampled success |
|---|---|---|---|
| baseline (stage 01) | 0, 0, 1 (3 seeds) | 0.062-0.078 | 0.144-0.210 |
| small-group (group_size=4) | 18, 4, 10 (3 seeds) | 0.024-0.050 | 0.032-0.080 |
| entropy-bonus (coef=0.01) | 0 (1 seed) | 0.078 | 0.176 |

**Neither fixed the collapse.** Small groups made every measured number
worse, consistently across 3 seeds -- more degenerate steps, lower greedy
and sampled success -- the opposite direction from Fan et al.'s finding, at
least at this reward shape and scale. The entropy bonus left both success
metrics essentially at baseline while measurably raising mid-training
entropy (1.3-1.7 nats, logged every 5 steps) -- confirming the bonus did
what it was designed to do (the distribution got less peaked) without
touching the one statistic greedy decode actually reads: which token wins
the argmax. Every configuration's greedy-decode examples still show one
fixed, board-independent completion (a repeated `RRRRRRRRRRRR`-style string
for the baseline shape, or, for small-group, a single-character `L`
followed immediately by EOS -- a strictly worse collapse than stage 01's).

That is the same divergence [stage 01](../01-grpo/#why-greedy-decode-collapsed-to-one-constant-board-independent-action)
lets you drive directly — and this stage's contribution is that none of the
three interventions moved it.

Full numbers, per-seed detail, and the collapsed examples themselves:
[`runs/2026-08-01-collapse-fix-sweep.md`](runs/2026-08-01-collapse-fix-sweep.md).

## Why this is still a useful result

Both are real negative findings, not a failure to find a fix worth hiding.
They narrow what "fixable" would require: not a training-signal tweak at
this scale, since the two most directly-motivated small interventions both
failed to move the argmax toward board-conditioning, one of them (smaller
groups) actively regressing every measured number. Per this mission's own
convention (mission 01's zero-gradient run, stage 01's own NOT MET), a
negative result stated plainly is the finding, not a placeholder for a
positive one.

## What this stage does not establish

Whether a larger model, more training steps, a different reward shape
(sparser or denser), or a combined intervention (both smaller groups and an
entropy bonus, or a KL-coefficient sweep, none of which were tried) would
fix the collapse -- none of those were varied here. Whether the collapse is
specific to this exact reward's two-part (format + success) shape. Only one
seed was run for the entropy-bonus variant (see the run record for why);
a promising direction would need the full 3-seed treatment before any claim.

**Next:** [stage 04](../04-minigrid/) moves to MiniGrid, a genuinely
partially-observed environment, and reports what happens to a cold-start
policy there -- interpreting the result knowing this stage found no fix for
stage 01's collapse.
