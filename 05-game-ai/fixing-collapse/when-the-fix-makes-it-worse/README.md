---
status: verified
level: applied
base: scratch
label: When the fix makes it worse
verified: 2026-08-06
---

# Both fixes failed, and one made the collapse strictly worse

**Question:** [stage 03's fixing collapse](../) tried two interventions
for the GRPO cold start. This chapter reads the recorded sweep and asks
what the failures establish.

**Before this:** [stage 03's fixing collapse](../) and its recorded sweep.

## The sweep, read

The run ([record](runs/2026-08-06-worse-read.md)) reads the recorded
results:

| variant | greedy success (per seed) |
|---|---:|
| baseline (group_size=8) | 0.078 / 0.062 / 0.078 |
| small-group (group_size=4) | 0.024 / 0.050 / 0.036 |
| entropy-bonus (coef=0.01) | 0.078 |

## Two readings

**Small-group made the collapse strictly worse.** The smaller group's
seeds produce single-character completions — 'L' followed immediately by
EOS, one step on every example — strictly worse than the baseline's
"repeat one legal action" pattern. The policy did not even learn to keep
emitting legal moves until the budget ran out. The recorded regression is
the point: an intervention can make a cold start worse, and the sweep
records it rather than hiding it.

**The entropy bonus reproduced the exact baseline failure.** With the
bonus, seed 0's greedy success (0.078) and its dumped examples
('RRRRRRRRRRRR', all 8) match stage 01's collapse exactly. Two fixes, two
ways to fail: one that changes nothing and one that makes it worse. The
recorded null says the training signal — not the group size or the
exploration — is the wall, which is the finding stage 03 exists to
document.

## The fix and its trade

The fix this detour contributes is the record of a regression, which the
mission treats as a finding rather than a failure to hide. Small-group
training produced single-character completions ('L' + EOS, one step on
every example) — strictly worse than the baseline's "repeat one legal
action" pattern — and the entropy bonus reproduced the baseline collapse
exactly. The trade is the honest one the sweep is built to make: an
intervention can make a cold start worse, and the recorded regression is
what tells a team the training signal itself is the wall, so a fix aimed
at group size or exploration would miss. The cost is that the null is a
null — it narrows the search space without offering a working fix, and the
diversity-direction detour (group 16) is where the mechanism actually
moved.

## Who owns this loop

- **The RL team** owns the intervention record and the regression rule:
  an intervention that makes the collapse strictly worse is a finding,
  reported beside the numbers, never edited out of the sweep.
- **The reward owner** owns the conclusion this regression feeds: two
  training-signal fixes failing points at the reward shape as the wall,
  which is the owner's suspect next.
- **The evaluation owner** owns the per-configuration comparability: all
  four configurations share the same grid-world, reward, and GRPO
  mechanism, which is what makes the small-group regression attributable
  to the group-size dial rather than to a changed environment.

## Evidence boundary

The recorded collapse sweep (one 5x5 grid-world, stage-01 reward and GRPO
mechanism, four configurations). It reads that artifact; it does not
re-train.

## Check your mental model

Answer each before opening it.

**1. Why does a smaller group make a cold start worse rather than better?**

<details>
<summary>Answer</summary>

Because a smaller group gives the group-relative advantage less signal to
work with. With group_size 4, the format-credit-only reward collapses the
whole group to the same degenerate behavior faster, and the policy
converges to emitting a single legal character and stopping. The recorded
single-step completions are that tighter collapse — the opposite of what
the fix was supposed to buy.

</details>

**2. What does "the training signal is the wall" mean for a next attempt?**

<details>
<summary>Answer</summary>

That neither the group size nor exploration changed the outcome, so the
fix has to be in the reward or the objective — not the hyperparameters
tried here. A reward whose format credit cannot be earned without the goal
is the direction the sweep points at; the recorded null is what rules out
the two cheaper hypotheses first.

</details>

## Next

Back to [stage 03](../), or to
[the one direction the collapse sweep never tried](../the-diversity-direction/)
which reads the same sweep's unexplored axis.
