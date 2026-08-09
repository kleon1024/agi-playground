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

<!-- interactive: CollapseFix -->

## Why this is still a useful result

Both are real negative findings, not a failure to find a fix worth hiding.
They narrow what "fixable" would require: not a training-signal tweak at
this scale, since the two most directly-motivated small interventions both
failed to move the argmax toward board-conditioning, one of them (smaller
groups) actively regressing every measured number. Per this mission's own
convention (mission 01's zero-gradient run, stage 01's own NOT MET), a
negative result stated plainly is the finding, not a placeholder for a
positive one.

## The fix and its trade

The interventions this stage tried each carry a real cost, and the sweep's
value is that it pays those costs and reports what they buy:

- **Smaller groups** (`group_size=4`) tests the Fan et al. (2025) finding
  that smaller rollout groups reduce collapse in classical RL. It is the
  cheapest test to run (same code path, one parameter), and it fails
  decisively here: degenerate steps rise to 4-18 per seed, and both greedy
  and sampled success fall below stage 01's baseline on all 3 seeds. The
  trade is now measured, not assumed: at this reward shape and scale,
  smaller groups cost variance the policy needs, in the opposite direction
  from the LLM-RLHF intuition where bigger groups usually help.
- **An entropy bonus** (`entropy_coef=0.01`) directly targets the argmax
  phenomenon. It does what it was designed to do -- mid-training entropy
  rises measurably (1.3-1.7 nats) -- yet greedy success stays at baseline
  (0.078). The trade is the important one: raising distribution entropy
  does not move *which token wins the argmax*, and the deployed policy
  reads only that token. The bonus buys diversity the serving path never
  sees.

The honest conclusion is that neither dial is the fix, and the stage says
so rather than tuning until something looks positive. A combined
intervention or a different reward shape remains untested and is named as
such in the boundary below -- the sweep narrows the space, it does not
claim to have searched it all.

## Who owns this loop

- **The RL team** owns the intervention sweep and its acceptance rule:
  a fix must move the *greedy* success metric, not training-time or
  sampled metrics, because deployment runs argmax.
- **The reward owner** owns the reward shape this sweep holds fixed. The
  result says the collapse resists training-signal dials at this scale,
  which is evidence that the reward's sparse board-credit shape is the
  suspect next -- a denser or shaped reward is the natural owner follow-up,
  not a retry of the same dials.
- **The evaluation owner** owns the per-seed reporting that keeps one
  favorable seed from being stretched into a fix. The entropy-bonus
  variant ran one seed; the boundary names that explicitly rather than
  letting a single draw read as a result.

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

A detour from here: [the one direction the collapse sweep never tried](the-diversity-direction/)
— the two missing cells of the same grid (group 16, entropy 0.05). Group 16
is the first variant that moves the collapse (greedy success 0.078 to
0.156), on one seed, which is exactly the kind of promising direction this
stage's boundary says would need the full 3-seed treatment next.

Another detour: [both fixes failed, and one made the collapse strictly worse](when-the-fix-makes-it-worse/) — the recorded sweep read: small-group produces single-character completions (worse than baseline) and the entropy bonus reproduces the exact failure, so the training signal is the wall.
