---
status: verified
level: applied
base: scratch
label: When the reward is wrong
verified: 2026-08-07
---

# The reward curve lies again — this time the labels are wrong or late

**Question:** the parent chapter showed a rising reward curve lying when the
policy hacks a *correct* reward. This detour breaks the label supply instead:
what does GRPO actually push toward when a slice of the correctness labels is
flipped, or when the ground truth drifts and the label lags a few steps behind
— and which signal tells you the curve is lying before you act on it?

**Before this:** [the reward went up](../) built the two knobs this detour
depends on — the within-group advantage and the held-out verifier — and
measured the curve lying when the reward is correct but gameable. This detour
reuses the same trainer and the same arithmetic task, and runs on the real
04-rl GRPO loop, not a new implementation.

## The setup is the parent's Exercise 1, executed

[The parent chapter](../) opens with a failure you have to see before
anything else works: from a cold start, every one of 200 GRPO groups is
degenerate — no completion parses into the `<answer>` tag the reward
requires, so the within-group advantage is zero everywhere and training never
starts. That is why its Exercise 1 asks for a warm start: a handful of
supervised steps on well-formed examples, just enough for the policy to emit
the format.

This detour executes that warm start ([run record](runs/2026-08-07-poisoned-reward-audit.md)):
250 supervised steps over 24 hand-written examples lift the tag fire rate from
"nothing fires" to 79.2% — 76 of 96 completions carry the `<think>/<answer>`
format the reward needs, against the base run's 200/200 degenerate groups
([base run record](../../runs/2026-07-30-base-grpo-run.md)). GRPO now has real
groups to normalize. That part is not the lesson; it is the precondition that
makes the lesson measurable.

## A flipped label moves the decision, not just the score

The run rolls out 20 groups of 8 completions and scores each group twice:
under the true labels and under labels where a fraction is flipped. GRPO's
advantage subtracts the group mean and divides by the group standard
deviation, so a flipped label does not average out across the group — it
reorders who the group pushes up.

| flip rate | groups that push a different completion | pushed completion wrong |
|---:|---:|---:|
| 5% | 2 of 20 (10%) | 2 of 20 |
| 10% | 7 of 20 (35%) | 7 of 20 |
| 20% | 12 of 20 (60%) | 12 of 20 |

The score only gets slightly noisier — the poisoned ranking's correlation
with the true ranking slides from 0.478 at 5% to 0.403 at 20% — but the
decision moves much more than the score does. Every time the poison changed
which completion the group pushes, the pushed completion was the wrong one.
That asymmetry is the first thing to internalize: a small label-error rate
looks like a small number, but the unit of learning is the group choice, and
the group choice is what flips.

This is not an arithmetic-task curiosity. RLHF's reward comes from human
preference comparisons, and preference labels are exactly the data an
attacker can corrupt a slice of. Rando and Tramèr (ICLR 2024,
[arXiv:2311.14455](https://arxiv.org/abs/2311.14455)) show that poisoning
RLHF preference data embeds a trigger word that acts like a universal "sudo
command": add the trigger to any prompt and the model produces harmful
output, with no adversarial prompt search needed. The poisoned human feedback
survives into the deployed policy — the same "poison does not stay where
injected" property Wan et al. (ICML 2023,
[arXiv:2305.00944](https://arxiv.org/abs/2305.00944)) measure for instruction
tuning, where a few poisoned examples generalize to held-out tasks.

## Both curves rise — and that is the point

Then the run compares two 30-step GRPO trainings with the same seed and
problem stream: clean labels versus 10% flipped. Both reward curves rise
across the steps. The poisoned arm's reward runs visibly higher — roughly
0.2–0.4 against the clean arm's 0.1–0.3 — while held-out true correctness
stays near zero in both arms, reaching only 0.1–0.2 in the late steps.

Two consequences follow. First, a team watching only the training curve will
conclude the poisoned run is going *better*: the flipped labels make the task
look easier, and the reward happily rises against them. Second, the detection
is the pair, not the curve: the clean held-out verifier is the only signal
allowed to disagree with the training reward, and disagreement above a
pre-written threshold is the stop condition. The parent chapter names this
reading rule for reward hacking — rising reward with flat held-out success is
evidence the policy found a feature that does not transfer. The same rule
catches a different cause here: the labels themselves are untrustworthy, not
the policy.

## A stale label is a poisoned label

The last arm of the run prices delay as poison. The truth flips with
probability `drift` each step, and the label used at training time reflects
the truth `lag` steps ago. Agreement with current truth follows
`0.5 + 0.5 (1 − 2·drift)^lag`:

| drift | lag 1 | lag 5 | lag 10 | lag 20 |
|---:|---:|---:|---:|---:|
| 2% | 97.8% | 90.5% | 83.0% | 71.7% |
| 5% | 94.6% | 78.6% | 67.4% | 55.5% |

At drift 5% and lag 20, the label is a coin flip: 55.5% agreement with current
truth. The first-order rule — error ≈ drift × lag — holds at small drift ×
lag and saturates at 50% for a binary label, because once the drift has
decorrelated the label from the truth, the two agree half the time by chance.
"The labels will be refreshed soon" is therefore not a reason to tolerate
staleness: the error budget belongs in the label pipeline — how fresh is fresh
enough, and what lag the monitoring will tolerate — not in the optimizer. The
same family shows up wherever ground truth moves and the label lags, and the
fix has the same shape: [a conversion that happens tomorrow is labeled a
negative today](../../../../02-personalized-discovery/recommendation/57-delayed-feedback/),
where the recommendation track runs the same freshness-versus-correctness
trade on conversion labels.

## Who owns it

The label pipeline owns label trust: poison-rate sampling, staleness
monitoring, and the "fresh enough" budget. The eval team owns the held-out
verifier and the disagreement threshold that stops a run. The model team
consumes clean labels and owns the training-reward/verifier pair as a run
contract, written before training starts — the same way the parent chapter's
stop conditions are written before the curve exists.

## The fix and its trade

The fix is the label-trust pipeline: poison-rate sampling on the incoming
label stream, a staleness budget that prices delay as poison (the delay
arm's label-agreement decay, `0.5 + 0.5 (1 - 2·drift)^lag`, a coin flip at
drift 5% / lag 20), and the training-reward/held-out-verifier pair as the
disagreement signal that stops a run when the labels lie. The trade,
named: freshness versus correctness — cutting the label window short
shrinks staleness but loses the delayed feedback that was the reason the
window existed, and tighter poison-rate sampling costs label-review
throughput. The verifier disagreement threshold costs the same thing
every guardrail costs: it can stop a run whose labels are actually fine,
which is why the threshold has to be declared before the curve exists,
not tuned against it.

## What this chapter does not prove

This is a mechanism demo: a toy char-level policy, a deterministic single
seed, and a hand-written warm-start set. It shows *that* flipped and delayed
labels distort the group choice and *that* the training curve cannot vouch
for its labels — not the magnitude on a production checkpoint. The
real-world magnitude is carried by the dated external work: poisoned
preference data embedding a universal trigger (Rando and Tramèr, ICLR 2024),
and a few poisoned instruction examples surviving into held-out behavior (Wan
et al., ICML 2023). The delay arm is a deterministic model of staleness, not
a measurement of a real label pipeline.

## Check your mental model

Answer each before opening it.

**1. Why does a 5% flip change 10% of group choices?**

<details>
<summary>Answer</summary>

The unit of learning is the group choice, not the score. GRPO normalizes the
advantage within the group, so a flipped label reorders the ranking; a 5%
label-error rate lands on enough groups that 1 in 10 ends up pushing a
different completion — and when the choice changes, it changes to the wrong
completion.

</details>

**2. Why can't you detect poisoned labels by watching the training reward?**

<details>
<summary>Answer</summary>

Because the poisoned arm's reward rises *higher* than the clean arm's — the
flipped labels make the task look easier, and the optimizer happily maximizes
the corrupted objective. The detection has to be a signal allowed to
disagree: a clean held-out verifier, watched as a pair with the training
reward.

</details>

**3. A stale label's error saturates at 50% — why not worse?**

<details>
<summary>Answer</summary>

The label is a binary guess about a binary truth that drifts; when drift has
decorrelated the two, the lagged label agrees with current truth half the
time by chance. 55.5% agreement at drift 5% and lag 20 is already a coin
flip, so the saturation point is not comfort — it is the end of the useful
label.

</details>

## Next

Return to [the reward went up](../) — its Exercise 1 is now executed, and its
signal list reads as the detection contract this chapter applies — or follow
the label-supply thread to [the KL leash](../../the-kl-leash/), which shows
what keeps the policy near the reference while the reward does whatever it
does. If the label pipeline is the target, the delayed-feedback chapters in
recommendation ([57](../../../../02-personalized-discovery/recommendation/57-delayed-feedback/))
run the same freshness-versus-correctness trade on conversion labels.
