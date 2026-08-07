---
status: verified
level: applied
base: scratch
label: Recommendation RLHF
verified: 2026-08-07
---

# The ranker learns which item the user preferred

**Question:** every ranker so far was trained on labels or click
proxies. This stage asks how a ranker learns when the supervision is a
pairwise preference — which item the user would rather see — and
answers: through the Bradley-Terry log loss, the same objective that
shaped the RLHF models this mission reuses.

**Before this:** [stage 04 — fine-rank](../04-fine-rank/) for
multi-objective prediction, and [mission 01's RL
stage](../../01-language-model-agent/04-rl/) for where the preference
objective came from.

## The loss, executed

The run ([record](runs/2026-08-07-recommendation-rlhf.md)) computes the
Bradley-Terry log loss over three preference pairs:

| chosen | rejected | logit | p(chosen) | loss |
|---|---:|---:|---:|---:|
| 1.2 | 0.4 | 0.8 | 0.69 | 0.37 |
| 0.9 | 0.8 | 0.1 | 0.52 | 0.64 |
| 0.3 | 1.1 | -0.8 | 0.31 | 1.17 |
| total | | | | 2.19 |

## The mechanism, named

The model scores both items, takes the sigmoid of their difference, and
is pushed to maximize the probability that the chosen item outscores
the rejected one. The loss is the negative log of that probability —
the weakest pair contributes 1.17 of the 2.19 total, so the model
spends most of its capacity fixing the preference it gets most wrong.
That is the RLHF shape: optimize over sampled pairs, not over labels.

## Why this belongs in the mission

Preference data is what a discovery system actually collects — users
choose between options, they do not label scores. RLHF is how a
recommender consumes that signal, and it brings the frontier failure
modes with it: noisy labels and a reward that can be gamed. The two
detours price both, which is the mission's way of stating that
preference optimization is not a model swap but a data-quality
discipline.

## Evidence boundary

The executed loss over three declared pairs with assumed scores
(illustrative, deterministic). It demonstrates the objective; real
preference optimization needs sampled pairs at scale, a policy to
regularize, and held-out human evaluation, which the detours quantify.

## Check your mental model

Answer each before opening it.

**1. Why does the loss grow when the model already prefers the rejected
item?**

<details>
<summary>Answer</summary>

Because the objective is to maximize the probability of the observed
preference. When the rejected item scores higher (logit -0.8, the
third pair), the model assigned most probability to the wrong choice,
and the negative log of the correct probability is large — 1.17. The
gradient then pushes the scores apart, which is how one wrong label
becomes a wrong gradient.

</details>

**2. How is this different from stage 04's multi-objective fine-rank?**

<details>
<summary>Answer</summary>

Stage 04 predicts several absolute quantities per item — click, dwell,
completion — from logged features. RLHF consumes a relative signal:
which of two items the user preferred. The first needs labels that are
calibrated; the second needs preferences that are correct, and a
correct preference between two noisy choices is a harder data problem,
which is the noisy-preference detour's point.

</details>

## Next

The frontier recommendation track continues. Next is [stage 33 —
multimodal recall](../33-multimodal-recall/), where content vectors
make cold items retrievable.

A detour from here: [the preference label is noisy and sets a loss
floor](when-the-preference-is-noisy/) — the executed flip read: one
flipped pair out of three sets a 0.80 wrong-gradient loss that the
clean pairs cannot remove, so the frontier cost is label quality.

Another detour: [the reward is gamed by the policy that maximizes
it](when-the-reward-is-gamed/) — the executed proxy read: the
sycophantic policy scores 0.9 on the proxy against 0.35 true quality,
so the gap between proxy and truth is reward hacking, and RLHF needs
regularization and held-out evals.
