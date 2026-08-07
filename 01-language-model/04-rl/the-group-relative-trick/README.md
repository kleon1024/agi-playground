---
status: verified
level: applied
base: scratch
label: The group-relative trick
verified: 2026-08-06
---

# What does the group-relative trick actually change?

**Question:** GRPO's one departure from PPO is the advantage — instead of a
learned critic's estimate, it uses a group statistic. [Stage 04](../)
derives the formula; this chapter runs the formula on the groups the real
runs produced, so the trick's three consequences — normalization, degeneracy,
clipping — are numbers, not claims.

**Before this:** [stage 04's RL run](../) and its 200/200 zero-gradient null.

## The formula, once

For one prompt, the policy samples G completions, the verifier scores them,
and the advantage of member i is:

```
A_i = (r_i - mean(r)) / (std(r) + 1e-4)
```

with std computed over the group, matching `core/grpo.py` exactly. Everything
about the method follows from this one line — and the stage's
[GRPOAdvantage widget](../#the-group-relative-trick) lets you move the rewards
and watch it live.

## The three measured cases

[`core/group_advantage.py`](core/group_advantage.py) runs the arithmetic on
three groups; the full output is in
[the run record](runs/2026-08-06-group-advantage.md).

**The degenerate group.** All eight completions score exactly 0.0 — the
group mission 01 hit on all 200 of 200 steps. std is 0, the advantage is 0/0,
and the group contributes no gradient. This is not a rare corner: an easy
prompt the policy already answers identically every time produces exactly
this, which is why skipping degenerate groups is the standard fix.

**A sparse group.** Two wins in eight, verifier reward 1.0 for a win and 0.0
otherwise: the winners carry advantages of +1.732 and the six losers -0.577.
Group normalization concentrates the update on the members that separated
themselves — the two winners absorb the whole push, which is the mechanism
behind mission 06's "1 of 200 steps degenerate" (legal moves plus a terminal
goal give the policy just enough variance for the statistic to exist).

**A healthy spread.** Rewards from 0.2 to 1.0: advantages from -1.428 to
+1.520, four members pushed up, four down. The group has enough variance
that every member gets a direction, and the mean-zero property of the
statistic means the update is always zero-sum across the group.

## What the clip adds

The loss does not apply the raw advantage. With ratio = exp(new log-prob
minus old log-prob) and epsilon 0.2, the objective uses
min(ratio*A, clip(ratio, 0.8, 1.2)*A): a positive-advantage member cannot be
pushed past 1.2x its old probability in one step, while the negative side is
not capped. The clip is a one-sided brake — it stops one good group from
driving the policy arbitrarily hard, which is the pessimistic bound
`grpo_loss` implements and the reason GRPO stays stable without a critic.

## Evidence boundary

This chapter computes the advantage statistic on synthetic groups mirroring
the recorded runs; it does not train a model, does not measure KL drift, and
does not claim the clip is optimal. The group values are the run records'
shapes, not new rollouts.

## Check your mental model

Answer each before opening it.

**1. Why does a group where every member scores the same contribute nothing,
even when the score is nonzero?**

<details>
<summary>Answer</summary>

Because the advantage is a difference from the group mean divided by the
group standard deviation. With zero variance the numerator is zero for every
member and the denominator is zero too — 0/0 — so there is no direction for
the update to move. The group contains no information about which member to
prefer, and GRPO's response is to skip it.

</details>

**2. In the sparse group, why do the two winners carry three times the
advantage magnitude of the losers?**

<details>
<summary>Answer</summary>

Because normalization divides by the group std, which is small when most
members are identical. The two 1.0s sit 0.75 above the 0.25 mean and the six
0.0s sit 0.25 below; after dividing by std 0.433 the winners get +1.732 and
the losers -0.577. The statistic concentrates credit on the few members that
separated themselves, which is the property that makes sparse verifier
rewards trainable at all.

</details>

## Next

Back to [stage 04's RL run](../) and its verdict, or forward to
[mission 06's GRPO stages](../../../05-game-ai/01-grpo/) where the same loop
meets a game's verifiable reward.
