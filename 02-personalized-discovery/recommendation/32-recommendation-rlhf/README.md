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

**Before this:** [stage 04 — fine-rank](../../shared/04-fine-rank/) for
multi-objective prediction, and [mission 01's RL
stage](../../../01-language-model/04-rl/) for where the preference
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

## How you find it: the margin-stratified pair audit, executed

The preference objective has a failure mode the label-based ranker
never faces: when two items score almost the same, label noise decides
which one is reported as chosen, and the model learns a wrong gradient
from a preference that was never really there. The aggregate loss
cannot see it — the near-tie pairs and the wide-margin pairs are
pooled. The run ([record](runs/2026-08-07-pair-margin-audit.md))
emits a 20-pair log, stratifies the pairs by margin, and reports the
flip rate under label noise:

| stratum | pairs | mean margin | flips | clean loss | observed loss |
|---|---:|---:|---:|---:|---:|
| head | 10 | 1.140 | 0 | 0.280 | 0.280 |
| tail | 10 | 0.039 | 4 | 0.674 | 0.689 |

The verdict is NEAR-TIE PREFERENCES FLIP UNDER LABEL NOISE: head pairs
(mean margin 1.14) are stable at 0/10 flips, while tail pairs (mean
margin 0.04) flip at 4/10 — the reported preference contradicts the
true one and forces a wrong gradient. The aggregate flip rate of 0.20
hides that every flip is a near tie. Rafailov et al. ("Direct
Preference Optimization", NeurIPS 2023, arXiv:2305.18290) is the
objective reference — the model optimizes the same Bradley-Terry log
loss this audit measures — and Zhang et al. ("Beyond Bradley-Terry
Models", ICML 2025, arXiv:2410.02197) is the limitation reference.
The decision that follows: sample pairs by margin, re-ask low-margin
preferences, and evaluate on high-margin held-out pairs.

<!-- interactive: RecommendationRlhf -->

## The fix and its trade

The fix is margin-aware preference handling: sample pairs by margin,
re-ask low-margin preferences instead of trusting the first answer, and
evaluate on high-margin held-out pairs. The executed audit prices the
failure — head pairs (mean margin 1.140) flip 0 of 10 under label
noise while tail pairs (mean margin 0.039) flip 4 of 10, so the
aggregate flip rate of 0.20 hides that every flip is a near tie and
every flip forces a wrong gradient the clean pairs cannot remove.

The trade is that the repair taxes annotation throughput: re-asking
low-margin pairs costs label budget and slows the pipeline, and
evaluating on high-margin held-out pairs is optimistic relative to
production, where near-ties dominate real preference streams. The
alternative — trusting the pooled loss — lets the weakest pair dominate
the gradient, exactly as the 1.17 of 2.19 total loss shows in the main
read. The margin stratification (Rafailov et al., NeurIPS 2023,
arXiv:2305.18290; Zhang et al., ICML 2025, arXiv:2410.02197) is what
makes the trade visible instead of buried in an aggregate.

## Who owns the loop

The ranker learns from preferences, and every handoff around that
signal is where RLHF fails:

- **The labeling or annotation team** owns the pairs: who marks which
  item was preferred, the agreement checks that catch flipped labels,
  and the re-ask policy for low-margin preferences. The
  [when-the-preference-is-noisy detour](when-the-preference-is-noisy/)
  is its failure mode — one flipped pair sets a wrong-gradient loss
  floor the clean pairs cannot remove.
- **The ranking or model team** owns the objective: the pair sampling
  distribution, the margin-aware weighting, and the choice between a
  scalar Bradley-Terry reward and a context-dependent preference
  model. The [when-the-preference-cycles
  detour](when-the-preference-cycles/) is its failure mode — a cycle
  is not a label error, it is the scalar model claiming an order that
  does not exist.
- **The evaluation team** owns the held-out preference sets, the
  high-margin gating of offline metrics, and the online reward check.
  The [when-the-reward-is-gamed
  detour](when-the-reward-is-gamed/) is its boundary — a proxy that
  can be maximized without improving the product is a reward, not a
  measure.

When the ownership is implicit, annotators mark near-ties confidently,
the model team optimizes whatever pairs arrive, and nobody owns the
tail — so the aggregate flip rate of 0.20 approves a ranker whose tail
preferences are label noise.

## Why this belongs in the mission

Preference data is what a discovery system actually collects — users
choose between options, they do not label scores. RLHF is how a
recommender consumes that signal, and it brings the frontier failure
modes with it: noisy labels, a reward that can be gamed, and a
preference that is not even a consistent order. The three detours
price them, which is the mission's way of stating that preference
optimization is not a model swap but a data-quality discipline.

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

And a third: [the preference the scalar model cannot
hold](when-the-preference-cycles/) — the executed cycle read:
for A > B, B > C, C > A the fitted ratings never settle (swing 0.659
after 1,000 iterations) and 2 of 3 edges are predicted wrong, so the
pipeline has to detect cyclic triples and drop the weakest edge or
model the preference as context-dependent.
