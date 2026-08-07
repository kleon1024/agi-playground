---
status: verified
level: applied
base: scratch
label: The reward went up
verified: 2026-07-30
---

# The reward went up. Did the model get better?

[The previous chapter](../) built GRPO against a verifiable reward: sample a
group, score each completion, normalize the advantage within the group, update.
Run it and the reward curve climbs. That curve is real — the scorer is not
lying, and the policy really is getting more of what you asked for.

This chapter is about the gap between *what you asked for* and *what you
wanted*, which in reinforcement learning is not a philosophical remark but the
default outcome. You need the loss function and the reward from the previous
chapter; you leave knowing which knob holds the policy back, why the reward you
had to design is the same reward that gets exploited, and what a rising curve
does not tell you.

## The leash: what the KL term is actually for

`grpo_loss` adds `kl_beta * kl` to the per-token loss, where `kl` is a k3
estimate of `KL(pi_theta || pi_ref)` against a frozen reference policy cloned
at the start of training.

Delete that term and nothing in the loss says "stay near where you started."
The policy is then free to drift arbitrarily far chasing reward, and it will —
settling on degenerate token sequences that slip past a regex edge case rather
than doing arithmetic. The reference policy is the only thing in the objective
that remembers what the model was before optimization began.

`beta` is the field's primary instability knob, and it fails in both
directions:

| `beta` | Failure |
|---|---|
| too small | the policy hacks the reward faster than the leash tightens |
| too large | every gradient step is cancelled by the divergence penalty and the policy barely moves |

There is no value that is safe for all of training, which is why production
recipes use adaptive KL controllers — target a specific KL value and scale
`beta` against the gap — rather than the fixed coefficient this lesson uses for
readability.

## A Python function is a much smaller thing to exploit

Before the exploits, be clear about how much a verifiable reward has already
removed. RLHF's reward comes from a learned reward model trained on human
preference comparisons — itself a neural network, with its own failure modes,
its own drift as the policy's outputs move away from what it was trained on,
and its own blind spots. RLVR replaces that with a programmatic verifier: does
this arithmetic answer match the computed ground truth, does this code pass its
test suite, does this proof check. `compute_reward` in
[the parent chapter](../README.md) is the entire "reward model" — a Python
function, not a trained one.

What that buys: no reward-model training run, no reward-model drift, and a much
smaller surface to exploit. A rule that computes `13 * 17` cannot be flattered
by sycophantic phrasing or a confident tone the way a learned reward model can.
This is why RLVR and math or code tasks are so tightly associated — a rule-based
reward only works where a verifier exists, but where one does, it sidesteps
almost the entire problem of hacking a learned model.

*Almost.* The surface is smaller, not zero, and the rest of this chapter is
what remains of it.

## The reward you had to design is the reward that gets exploited

Why not reward correctness alone and skip the format reward? Because a 0/1
correctness signal gives a cold-start policy almost no gradient. Early in
training the policy essentially never emits a parseable `<answer>N</answer>`,
so every completion scores exactly 0, every group is degenerate — identical
scores mean identical advantages mean no gradient — and `rollout_and_score`
discards all of them. Nothing happens, forever.

The format reward's partial-credit ladder exists to give the policy something
to climb before it can possibly get the arithmetic right: 1.0 for well-formed
`<think>`/`<answer>` tags, 0.5 for both tags present but malformed, 0.2 for
one, 0.0 for neither.

And that ladder is exactly what gets farmed. **Any reward shaped to make
partial progress visible is, by construction, also a reward partially
satisfiable without doing the real task.** This is not a defect in this
lesson's reward function. DeepSeek-R1's paper reports navigating the identical
tension for the identical cold-start reason, resolving it the same way: weight
correctness so it dominates.

Which is why `compute_reward` puts `format_weight` at 0.2 and
`correctness_weight` at 1.0, and why the ordering is the load-bearing part
rather than the specific values.

## Three hacks to watch for in this exact task

- **Format-only optimization.** The format reward pays 0.2–1.0 regardless of
  whether the answer is right. A policy that finds well-formed tags easier than
  arithmetic will farm it with a plausible but wrong answer, whenever the
  correctness signal is too weak relative to it.
- **Regex-edge exploitation.** `_ANSWER_RE` matches the *first*
  `<answer>N</answer>` in the text. A policy could learn to emit several answer
  tags and bet that one matches — a toy-scale instance of what motivates DAPO's
  overlong-response reward shaping. Real RLVR setups need explicit handling for
  plausible-looking cheating, not just a correctness check.
- **Length and verbosity drift.** Nothing penalizes a needlessly long `<think>`
  block. At scale this is the same phenomenon as RLHF's documented length bias,
  arriving through a different door: an unconstrained action space rather than
  a biased scorer.

## The measured reward and the thing you wanted diverge on purpose

Gao, Schulman, and Hilton (*Scaling Laws for Reward Model Overoptimization*,
2023) give the quantitative version. True quality follows an inverted U in KL
divergence from the reference policy, approximately

```text
gold_score  ≈  a·sqrt(KL)  −  b·KL
```

so there is a real optimum past which **the measured reward keeps climbing
while actual quality falls**. Before that point, moving away from the reference
policy buys you genuine improvement. After it, you are buying the scorer's
blind spots.

The practical consequence is that a rising reward curve is not evidence of
anything on its own. You need the KL divergence plotted beside it, and a held-
out check that does not use the training reward — otherwise the instrument
measuring success is the same instrument being optimized against.

Reward hacking is the default outcome of unmitigated reinforcement learning,
not an edge case that careful reward design avoids.

## A real run: the exercise below cannot fire yet

Exercise 1 asks to remove the leash (`--kl-beta 0`) and watch reward and a
held-out correctness check separate. Run it against [the exact same seed as
the parent chapter's base run](../runs/2026-07-30-base-grpo-run.md) and the
result is identical: every one of 200 groups is degenerate, so `grpo_loss`
— the only place `kl_beta` is used — is never called. Setting `kl_beta` to 0
changes nothing observable, because the gate it would affect is never
reached. [Full run.](runs/2026-07-30-kl-beta-zero-ablation.md)

None of the three hacks below is claimed to have been observed in this
repository — they are the failure modes the reward function's shape makes
available, named in advance so they are recognizable once training actually
starts. The inverted-U result is external, attributed, and measured on
reward *models* rather than the verifiable rewards this stage uses; the
mechanism transfers, the specific coefficients do not.

## Which signals have to disagree before you believe the curve

One number cannot catch reward hacking, because the hacked reward is the number
going up. What catches it is a set of signals that are *allowed to disagree*,
watched together:

```text
training reward
held-out verifier success
response length and format
KL from reference
diversity within each group
manual high-reward failure rate
baseline capability regressions
```

Rising training reward with flat held-out success is not slow progress. It is
evidence the policy found a feature of the training reward that does not
transfer — the inverted-U above, caught early rather than at the far side.
The same reading rule catches a second cause, and it is executed in
[when the reward is wrong](when-the-reward-is-wrong/): the labels themselves
— flipped or stale — make the curve lie while the policy is innocent, and the
training-reward/verifier pair is the signal that tells the two apart.

Which is why the stop conditions belong in the run contract, written before the
run: a maximum KL, a regression tolerance on the baseline capabilities, an
invalid-output rate, and the manual-audit threshold that says how many
high-reward completions a human reads before the number is allowed to count.
None of those can be chosen honestly once you are looking at the curve.

## Exercises

1. **Remove the leash, after a warm start.** The run above shows `--kl-beta 0`
   changes nothing on its own — training never starts. Warm-start the policy
   first (parent chapter's Exercise 1), then rerun with `--kl-beta 0` and plot
   reward against a held-out correctness check; identify the step where they
   separate.
2. **Invert the weights.** Set `format_weight` above `correctness_weight` and
   describe the completions after a few hundred steps before you look at them.
3. **Close the regex edge.** Change `_ANSWER_RE` to require exactly one
   `<answer>` tag and reject completions with more. What new hack does that
   make available?

## Check your mental model

1. Why does a correctness-only reward produce no gradient at all early in
   training, rather than merely a weak one?

<details>
<summary>Answer</summary>

Early in training the policy essentially never emits a parseable
`<answer>N</answer>`, so every completion in a group scores exactly 0 under a
correctness-only reward. GRPO's advantage is computed by normalizing within
the group — and when every score in the group is identical, the normalized
advantage is 0 for all of them, which `rollout_and_score` discards as
degenerate. A "weak" gradient would still be a nonzero number nudging the
policy somewhere; this is a hard zero, produced structurally by every
completion tying, not by the signal being small.

</details>

2. The format reward exists to solve cold start and is the thing that gets
   farmed. Is that a design mistake, and what would replace it?

<details>
<summary>Answer</summary>

Not a design mistake — the chapter states this directly: "any reward shaped
to make partial progress visible is, by construction, also a reward partially
satisfiable without doing the real task." That's an inherent property of
partial-credit shaping, not a fixable flaw in this particular reward
function; DeepSeek-R1's paper reports navigating the identical tension for
the identical cold-start reason. The mitigation isn't replacing the format
reward with something unfarmable — it's weighting correctness so it
dominates (`correctness_weight=1.0` against `format_weight=0.2`), so the
format reward can still solve cold start without becoming the policy's
easiest path to reward.

</details>

3. Reward is rising and KL is rising. Which of those two tells you the model is
   improving, and what third measurement settles it?

<details>
<summary>Answer</summary>

Neither alone tells you the model is improving. The Gao/Schulman/Hilton
inverted-U result says true quality rises with KL divergence only up to a
real optimum, past which measured reward keeps climbing while actual quality
falls — so a rising reward curve is "not evidence of anything on its own,"
and rising KL just says the policy has moved further from the reference,
which could be genuine improvement or could be exploiting the scorer's blind
spots. The third measurement that settles it is a held-out check that does
not use the training reward — otherwise the instrument measuring success is
the same instrument being optimized against.

</details>

4. What does the frozen reference policy contribute to the objective that no
   term computed from the current policy could?

<details>
<summary>Answer</summary>

A fixed point of comparison to what the model was *before* optimization
began. Every term computed from the current policy only knows where the
policy is now (or was a step ago); it has no memory of the starting point.
The KL term against the frozen reference is "the only thing in the objective
that remembers what the model was before optimization began" — delete it and
nothing in the loss says "stay near where you started," so the policy is
free to drift arbitrarily far chasing reward, settling on degenerate
sequences that exploit scorer edge cases rather than doing the real task.

</details>

5. Under what circumstance would you accept a lower measured reward as the
   better result?

<details>
<summary>Answer</summary>

When the held-out correctness check (not the training reward) shows the
higher-reward checkpoint is actually past the inverted-U's optimum —
climbing reward but falling true quality, per the Gao/Schulman/Hilton
result. In that case the checkpoint with the lower training-reward score but
the better held-out score is the one that's actually solving the task rather
than exploiting the verifier's blind spots, and preferring it means trusting
the measurement that isn't the same instrument being optimized against.

</details>

## Next

Return to [stage 04](../) to run it, then [stage 05](../../05-serve/) serves
whatever policy comes out — where the cost of those longer `<think>` blocks
stops being a training-time curiosity and becomes tokens somebody waits for.
