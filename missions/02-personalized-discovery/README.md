---
status: draft
level: applied
---

# Personalized discovery

**Business goal:** reduce the time it takes a user to find something worth
their attention, without degrading what the catalogue offers them or what the
platform earns.

Recommendation, search, and advertising are one mission, not three, because
they are the same decision loop with different inputs. Recommendation ranks
with no query. Search ranks with one. Ads insert a paid item into either, and
**every ad displaces an organic result** — so the three cannot be optimized
independently without one quietly cannibalizing the others.

Read [`mission.yaml`](mission.yaml) first, especially `does_not_prove`.

## Why this mission exists

Mission 01 proved the platform layers compose. It did not prove they
*generalize*, because everything in it was a language model producing text.

This mission is the test of the architecture's central claim. Ranking is a
genuinely different decision loop: the objective is not next-token likelihood,
the model is usually not a transformer, and the failure modes — feedback loops,
popularity collapse, position bias — are ones text generation never has. If
`platform/` is a real set of layers rather than a relabelled LLM pipeline, this
should reuse it.

## The funnel, and why it has this shape

A production discovery system is a cascade of progressively more expensive
models over progressively smaller candidate sets. That structure is not
tradition; it is forced by arithmetic. Scoring ten million items with a good
model inside 100ms is impossible, so each stage buys the next one a smaller
problem.

<!-- interactive: RecommendationFunnel -->

Each stage exists for a reason worth stating precisely:

**Content understanding** turns raw items into features. This is where a VLM
earns its place: a video or product image carries information no interaction
log contains, and for cold items it is the *only* signal available. A newly
uploaded item has no clicks, so its embedding must come from its content or it
cannot be retrieved at all.

**Multi-queue recall** is plural on purpose. A single retrieval method has a
single blind spot, and the blind spots differ: a two-tower embedding model is
good at semantic similarity and bad at exact-match queries; lexical search is
the reverse; item-to-item covers "more like what you just engaged with";
freshness and business queues cover what statistics cannot. Production systems
run these in parallel and union the results, because recall is the one thing
downstream stages cannot repair — **a perfect ranker cannot rank an item that
was never retrieved.**

**Pre-rank** exists because the gap between "cheap enough for 10M items"
and "good enough to rank 20" is too wide to bridge in one model. It cuts ~1000
to ~100 with a model perhaps a hundredth the cost of the fine-ranker. Its
failure mode is subtle and worth a lesson of its own: if pre-rank and fine-rank
disagree systematically, pre-rank is silently deciding the result, and the
expensive model is decorative.

**Fine-rank** predicts several things at once — click, conversion, dwell
time, completion, satisfaction — because no single one of them is what you
actually want. This is where the heavy model goes.

**The value tree** is the step most tutorials omit and most production
arguments are about. Fine-rank produces a vector of predictions; ranking needs
a scalar. How you collapse them *is* the product strategy, expressed as
arithmetic: weights, multiplicative versus additive combination, calibration so
that a predicted 0.3 means 0.3, and explicit trade rates between user value and
revenue. Changing one weight changes what the platform is for.

**Mixing / re-rank** assembles the actual slate. Ranking items independently
and taking the top-K is wrong, because the value of a slate is not the sum of
its items: ten near-identical items score well individually and are a bad page.
This is a combinatorial problem over permutations, which is where beam search
and its relatives come in — and where paid placement is finally interleaved,
since an ad's cost is the organic item it displaced.

**The rule engine** carries everything that is a business fact rather than a
learned preference: legal blocks, regional availability, safety filters,
editorial boosts, per-creator caps. It must be separate from the models, because
these change on a policy timescale rather than a training timescale, and
because "why was this shown" needs an auditable answer.

## Start mini, then scale

The system above is a description of the destination. Building it in that order
would produce nothing testable for weeks, so the mission goes end-to-end small
first and deepens each stage afterwards:

**v0 — the whole funnel, deliberately crude.** Popularity recall, no pre-rank,
a linear fine-ranker on a handful of features, a single-objective value
function, top-K with a diversity penalty, one hard rule. On a catalogue small
enough to score exhaustively, so every approximation can be measured against
ground truth. This produces the baselines and the harness everything later is
compared against.

**v1 — deepen the stages that matter most, measured one at a time.** Two-tower
recall with real recall@1000 numbers, a genuine pre-rank with agreement
analysis against fine-rank, multi-objective fine-rank, the value tree with
calibration, beam-search slate assembly, the ads auction.

**v2 — scale.** Catalogue large enough that exhaustive scoring is impossible and
approximate nearest-neighbour search becomes mandatory, distributed training,
and serving inside the latency budget.

Each version must beat the previous one on the declared metric, or the added
complexity is not paid for. That rule is the entire defence against building an
impressive system that ranks worse than popularity.

## Stages

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`00-interactions`](00-interactions/) | Public interaction dataset, cleaned, split **by time** — a random split leaks the future | `platform/data` | implementation present; run pending |
| [`01-content-understanding`](01-content-understanding/) | VLM labelling of items into taxonomy + embeddings; cold-item coverage measured | `capabilities/perceive-understand` | verified synthetic mechanism run; mission outcome pending |
| [`02-recall`](02-recall/) | Multi-queue: two-tower, lexical, i2i, fresh; union and dedup; recall@1000 vs exhaustive | `capabilities/retrieve-ground` | implementation present; run pending |
| [`03-pre-rank`](03-pre-rank/) | Lightweight scorer, 1000→100, with pre-rank/fine-rank agreement analysis | `capabilities/rank-decide` | implementation present; run pending |
| [`04-fine-rank`](04-fine-rank/) | Multi-objective model: click, dwell, completion, satisfaction | `capabilities/rank-decide` | implementation present; run pending |
| [`05-value-tree`](05-value-tree/) | Objective combination, calibration, explicit user-value/revenue trade rates | `capabilities/rank-decide` | implementation present; run pending |
| [`06-mixing`](06-mixing/) | Slate assembly by beam search; diversity; ad interleaving with displacement cost | `capabilities/rank-decide` | verified synthetic mechanism run; mission outcome pending |
| [`07-rule-engine`](07-rule-engine/) | Declarative constraints, auditable decisions, policy-timescale changes | `platform/safety-governance` | verified synthetic mechanism run; mission outcome pending |
| [`08-serving`](08-serving/) | Two-stage serving inside p95 300ms; ANN index; measured | `platform/serving` | verified synthetic mechanism run; mission outcome pending |
| [`09-report`](09-report/) | Outcome vs both baselines and all guardrails, with failure cases | `platform/evaluation-observability` | verified evaluator run; outcome cannot determine |

## What makes this hard to prove

Mission 01 could claim "the stages ran". This mission wants to claim "users
found things faster", and that claim cannot be made here. There are no users.

The outcome is proven by **offline replay** — rank held-out interactions,
measure whether the true item ranks higher — with three limits stated up front
rather than buried:

1. **Logged data is confounded by the policy that produced it.** Users could
   only click what the previous system showed them. An offline win can vanish or
   invert online. This is the central methodological problem of the field.
2. **It cannot see what was never shown.** Novelty and discovery value are
   invisible to replay by construction.
3. **The ads component is simulated.** Bids come from a declared distribution,
   so it tests auction mechanics and user cost, not revenue.

**And it must beat popularity.** Un-personalized global popularity is a
famously strong baseline that many published recommender results fail to clear.
A system that cannot beat "show everyone the same popular items" has not
demonstrated personalization, whatever its nDCG looks like in isolation.

## What this reuses

Reuse is the point of the exercise: the data discipline from
[`platform/data`](../../platform/data/), the training engineering from
[`platform/training`](../../platform/training/) — gradient accumulation, mixed
precision, resumable checkpoints — the serving concerns from
[`platform/serving`](../../platform/serving/), and the evaluation discipline
from [`platform/evaluation-observability`](../../platform/evaluation-observability/),
where harness disclosure and seed variance already live.

New capabilities live inside this mission until a **second** mission needs them,
per the gate in [`standards/mission-contract.md`](../../reference/standards/mission-contract.md).
`perceive-understand` is the likely first graduate, since multimodal content
intelligence would reuse it directly.

## Sequencing

Mission 01 finishes before this one starts building. That ordering is
deliberate: this mission's value is demonstrating the platform layers are
reusable, and that claim is worthless while those layers are still being built.
What exists now is the contract and the architecture — which is exactly what
[`mission.yaml`](mission.yaml) requires before any code is written.
