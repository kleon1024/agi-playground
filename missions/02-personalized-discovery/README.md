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
popularity collapse, position bias — are ones text generation never has. If mission 01's stages
are genuinely reusable machinery rather than a relabelled LLM pipeline, this
mission should reuse them.

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

## Model lineage

The stages above are points on the recommender line — matrix factorization,
two-tower retrieval, sequence models, cascade ranking, slate assembly. The
[open-source line behind personalized discovery](../../reference/research/lineages/02-personalized-discovery.md)
traces each predecessor and the tradeoff it made.

## Stages

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`00-interactions`](00-interactions/) | Public interaction dataset, cleaned, split **by time** — a random split leaks the future | mission 01 · corpus | implementation present; run pending |
| [`01-content-understanding`](01-content-understanding/) | VLM labelling of items into taxonomy + embeddings; cold-item coverage measured | mission 01 · agent harness | verified synthetic mechanism run; mission outcome pending |
| [`02-recall`](02-recall/) | Multi-queue: two-tower, lexical, i2i, fresh; union and dedup; recall@1000 vs exhaustive | new to this mission | implementation present; run pending |
| [`03-pre-rank`](03-pre-rank/) | Lightweight scorer, 1000→100, with pre-rank/fine-rank agreement analysis | new to this mission | implementation present; run pending |
| [`04-fine-rank`](04-fine-rank/) | Multi-objective model: click, dwell, completion, satisfaction | new to this mission | implementation present; run pending |
| [`05-value-tree`](05-value-tree/) | Objective combination, calibration, explicit user-value/revenue trade rates | new to this mission | implementation present; run pending |
| [`06-mixing`](06-mixing/) | Slate assembly by beam search; diversity; ad interleaving with displacement cost | new to this mission | verified synthetic mechanism run; mission outcome pending |
| [`07-rule-engine`](07-rule-engine/) | Declarative constraints, auditable decisions, policy-timescale changes | mission 01 · eval gates | verified synthetic mechanism run; mission outcome pending |
| [`08-serving`](08-serving/) | Two-stage serving inside p95 300ms; ANN index; measured | mission 01 · serving | verified synthetic mechanism run; mission outcome pending |
| [`09-report`](09-report/) | Outcome vs both baselines and all guardrails, with failure cases | mission 01 · eval | verified evaluator run; outcome cannot determine |

### The search track (stages 10-13)

Search is the same decision loop with an explicit query. The four stages
below take the query from raw string to a ranked, evaluated result — the
search analogue of recommendation's recall-to-report funnel.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`10-query-understanding`](10-query-understanding/) | Tokenize, normalize, and classify the query; the key space retrieval must serve | new to this mission | verified mechanism run |
| [`11-search-retrieval`](11-search-retrieval/) | BM25 lexical index; the vocabulary-mismatch gap dense retrieval must close | new to this mission | verified mechanism run |
| [`12-search-ranking`](12-search-ranking/) | Pointwise vs pairwise ranking over the candidate set; NDCG as arbiter | new to this mission | verified mechanism run |
| [`13-search-evaluation`](13-search-evaluation/) | NDCG@k and MRR; the metric blind spots that force the declared choice | mission 01 · eval | verified mechanism run |

### The ads track (stages 14-18)

Ads insert a paid item into either surface, and every ad displaces an
organic result. The five stages below run the economics: allocation,
revenue ranking, calibration, delivery, and the displacement trade.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`14-ad-auction`](14-ad-auction/) | Second-price auction; truthful bidding as the dominant strategy | new to this mission | verified mechanism run |
| [`15-ecpm-ranking`](15-ecpm-ranking/) | Bid x pCTR revenue ranking; the lower bid that wins | new to this mission | verified mechanism run |
| [`16-ctr-calibration`](16-ctr-calibration/) | pCTR calibration (ECE) and the correction that makes the estimate honest | new to this mission | verified mechanism run |
| [`17-budget-pacing`](17-budget-pacing/) | Budget delivery under a per-hour cap; the feedback signal | new to this mission | verified mechanism run |
| [`18-ad-externality`](18-ad-externality/) | The displacement trade; scarcity amplifies the externality | mission 02 · value tree | verified mechanism run |

### The advanced search track (stages 19-24)

The four-stage search track (10-13) ran the query from raw string to
ranked result. The six stages below deepen it to production depth:
repair the query, add a meaning-based index, fuse the matchers, rerank,
personalize, and measure the queries that return nothing.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`19-query-expansion`](19-query-expansion/) | Query correction as retrieval pre-processing; recall recovered | new to this mission | verified mechanism run |
| [`20-dense-retrieval`](20-dense-retrieval/) | Two-tower cosine retrieval; the meaning-based index | new to this mission | verified mechanism run |
| [`21-hybrid-fusion`](21-hybrid-fusion/) | Reciprocal rank fusion of lexical and dense sets; the union kept | new to this mission | verified mechanism run |
| [`22-reranking`](22-reranking/) | Second ranker over the top-k; the latency-budget split | new to this mission | verified mechanism run |
| [`23-personalized-search`](23-personalized-search/) | Relevance plus user affinity; the query with a user attached | new to this mission | verified mechanism run |
| [`24-search-measurement`](24-search-measurement/) | Zero-result rate and its causes; the coverage signal | new to this mission | verified mechanism run |

### The advanced ads track (stages 25-30)

The five-stage ads track (14-18) ran the economics of a paid slot. The
six stages below add the delivery and measurement depth: cap
frequency, choose the creative, derive the bid, compare auction rules,
fit the 100ms deadline, and measure what the ad actually changed.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`25-frequency-capping`](25-frequency-capping/) | The exposure cap; CTR decay makes it a value decision | new to this mission | verified mechanism run |
| [`26-creative-selection`](26-creative-selection/) | Per-context creative choice; the creative feeds eCPM | new to this mission | verified mechanism run |
| [`27-bid-strategy`](27-bid-strategy/) | Target-CPA bid as value times conversion; the walk-away line | new to this mission | verified mechanism run |
| [`28-auction-revenue`](28-auction-revenue/) | First versus second price; the rule moves revenue | new to this mission | verified mechanism run |
| [`29-rtb-pipeline`](29-rtb-pipeline/) | The 100ms real-time bid; latency as a selection mechanism | new to this mission | verified mechanism run |
| [`30-ads-measurement`](30-ads-measurement/) | Incrementality against a control; the ad's actual effect | new to this mission | verified mechanism run |




## Where each stage leaves the path

A stage states a decision; these deep-dive chapters answer the decisions
the main path asserts without showing, mission-01 style — each returns an
artifact or a measurement the next stage consumes.

| At this stage | You need to decide | So read |
|---|---|---|
| `00-interactions` | The filter that catches users it did not aim at | [the-eligibility-cascade](00-interactions/the-eligibility-cascade/) |
| `00-interactions` | The 99.1% leak: what the wrong split actually buys | [when-the-split-leaks](00-interactions/when-the-split-leaks/) |
| `00-interactions` | The absence is a signal | [when-the-absence-is-a-signal](00-interactions/when-the-absence-is-a-signal/) |
| `01-content-understanding` | The behavioural floor the threshold cannot touch | [the-63-percent-that-never-moves](01-content-understanding/the-63-percent-that-never-moves/) |
| `01-content-understanding` | The confidence threshold: precision for the head, or reach for the tail? | [when-the-threshold-rescues-the-tail](01-content-understanding/when-the-threshold-rescues-the-tail/) |
| `01-content-understanding` | The label the threshold cannot trust | [when-the-label-is-noisy](01-content-understanding/when-the-label-is-noisy/) |
| `02-recall` | Recall bought back at a measured latency cost | [the-price-of-approximate](02-recall/the-price-of-approximate/) |
| `02-recall` | The queue you disable is the target you lose | [when-you-lose-a-queue](02-recall/when-you-lose-a-queue/) |
| `02-recall` | The tail that the index forgets | [when-the-tail-goes-cold](02-recall/when-the-tail-goes-cold/) |
| `03-pre-rank` | When does the cheap cut fail? | [when-the-cheap-cut-fails](03-pre-rank/when-the-cheap-cut-fails/) |
| `03-pre-rank` | The zero that is structural, not a tuning miss | [when-the-long-tail-is-invisible](03-pre-rank/when-the-long-tail-is-invisible/) |
| `03-pre-rank` | The cheap score that flips the cut | [when-the-cheap-score-lies](03-pre-rank/when-the-cheap-score-lies/) |
| `04-fine-rank` | Why ECE is a gate, not a polish step | [the-calibration-that-decides](04-fine-rank/the-calibration-that-decides/) |
| `04-fine-rank` | When does the shared model hurt an objective? | [when-sharing-hurts](04-fine-rank/when-sharing-hurts/) |
| `04-fine-rank` | The model that learned yesterday | [when-the-model-is-stale](04-fine-rank/when-the-model-is-stale/) |
| `05-value-tree` | The same strategy, different calibration, different slate | [the-calibration-break](05-value-tree/the-calibration-break/) |
| `05-value-tree` | The weight IS the strategy | [when-the-weight-moves](05-value-tree/when-the-weight-moves/) |
| `05-value-tree` | The dislike that flips the weight | [when-the-user-rejects](05-value-tree/when-the-user-rejects/) |
| `06-mixing` | A narrow beam finding the optimum is not proof a beam is enough | [when-the-beam-is-wide-enough](06-mixing/when-the-beam-is-wide-enough/) |
| `06-mixing` | What does a mixing weight actually trade off? | [when-the-trade-weight-moves](06-mixing/when-the-trade-weight-moves/) |
| `06-mixing` | The diverse slate that underperforms | [when-diversity-hurts](06-mixing/when-diversity-hurts/) |
| `07-rule-engine` | A rule engine's failure mode is interaction, not any single rule | [the-empty-set-was-two-rules](07-rule-engine/the-empty-set-was-two-rules/) |
| `07-rule-engine` | When does the rule engine return an empty set? | [when-the-rules-collide](07-rule-engine/when-the-rules-collide/) |
| `07-rule-engine` | The rule nobody tested | [when-the-rule-is-a-typo](07-rule-engine/when-the-rule-is-a-typo/) |
| `08-serving` | Means add for the serial path; tail percentiles do not | [when-p95s-do-not-add](08-serving/when-p95s-do-not-add/) |
| `08-serving` | What does the pre-rank cut buy, and when does it stop paying? | [when-the-cut-bites](08-serving/when-the-cut-bites/) |
| `08-serving` | The cache that misses together | [when-the-cache-goes-cold](08-serving/when-the-cache-goes-cold/) |
| `09-report` | A headline win that still loses, seed by seed | [the-variance-that-decides](09-report/the-variance-that-decides/) |
| `09-report` | A headline win that is still NOT MET | [when-the-guardrail-vetoes](09-report/when-the-guardrail-vetoes/) |
| `09-report` | The baseline that moved | [when-the-baseline-moves](09-report/when-the-baseline-moves/) |
| `10-query-understanding` | Where normalization stops and correction must begin | [when-the-query-is-misspelled](10-query-understanding/when-the-query-is-misspelled/) |
| `10-query-understanding` | One word, many intents | [when-the-query-is-short](10-query-understanding/when-the-query-is-short/) |
| `11-search-retrieval` | The document that means the same but scores less | [when-the-synonym-is-invisible](11-search-retrieval/when-the-synonym-is-invisible/) |
| `11-search-retrieval` | The embedding that sees the synonym | [when-the-dense-path-exists](11-search-retrieval/when-the-dense-path-exists/) |
| `12-search-ranking` | The label that carries the position's bias | [when-the-label-is-a-click](12-search-ranking/when-the-label-is-a-click/) |
| `12-search-ranking` | Where the formulation choice actually matters | [when-the-list-is-longer](12-search-ranking/when-the-list-is-longer/) |
| `13-search-evaluation` | The metric chooses the winner | [when-mrr-and-ndcg-disagree](13-search-evaluation/when-mrr-and-ndcg-disagree/) |
| `13-search-evaluation` | NDCG@1 is a different claim than NDCG@5 | [when-the-k-is-small](13-search-evaluation/when-the-k-is-small/) |
| `14-ad-auction` | The floor that can also kill the sale | [when-the-reserve-price-bites](14-ad-auction/when-the-reserve-price-bites/) |
| `14-ad-auction` | The dominant strategy is the honest one | [when-truthful-bidding-is-optimal](14-ad-auction/when-truthful-bidding-is-optimal/) |
| `15-ecpm-ranking` | The knife-edge the click estimate sits on | [when-pctr-moves-the-rank](15-ecpm-ranking/when-pctr-moves-the-rank/) |
| `15-ecpm-ranking` | The reserve and the ranking are one decision | [when-the-reserve-interacts](15-ecpm-ranking/when-the-reserve-interacts/) |
| `16-ctr-calibration` | The fix that makes the estimate honest | [when-the-correction-is-needed](16-ctr-calibration/when-the-correction-is-needed/) |
| `16-ctr-calibration` | Perfect order, wrong values | [when-calibration-and-ranking-conflict](16-ctr-calibration/when-calibration-and-ranking-conflict/) |
| `17-budget-pacing` | The cap that binds when demand spikes | [when-delivery-varies](17-budget-pacing/when-delivery-varies/) |
| `17-budget-pacing` | Pacing cannot create a budget | [when-the-budget-is-tiny](17-budget-pacing/when-the-budget-is-tiny/) |
| `18-ad-externality` | Scarcity amplifies the externality | [when-the-slot-is-scarce](18-ad-externality/when-the-slot-is-scarce/) |
| `18-ad-externality` | The externality flips sign when the ad is relevant | [when-the-ad-is-relevant](18-ad-externality/when-the-ad-is-relevant/) |
| `19-query-expansion` | The correction recovers what the raw query could not | [when-the-correction-helps](19-query-expansion/when-the-correction-helps/) |
| `19-query-expansion` | Expansion trades precision for recall | [when-expansion-hurts](19-query-expansion/when-expansion-hurts/) |
| `20-dense-retrieval` | Approximate is the only feasible index at scale | [when-the-index-is-ann](20-dense-retrieval/when-the-index-is-ann/) |
| `20-dense-retrieval` | The item without a vector is unreachable | [when-the-embedding-is-stale](20-dense-retrieval/when-the-embedding-is-stale/) |
| `21-hybrid-fusion` | The fusion weight is a trust decision | [when-the-fusion-weight-moves](21-hybrid-fusion/when-the-fusion-weight-moves/) |
| `21-hybrid-fusion` | The hybrid degrades into whoever is alive | [when-one-set-is-empty](21-hybrid-fusion/when-one-set-is-empty/) |
| `22-reranking` | The cutoff decides what the reranker can fix | [when-the-rerank-budget-is-tight](22-reranking/when-the-rerank-budget-is-tight/) |
| `22-reranking` | Disagreement is the reranker's job and its risk | [when-the-reranker-disagrees](22-reranking/when-the-reranker-disagrees/) |
| `23-personalized-search` | History is a prior over the query | [when-the-user-history-helps](23-personalized-search/when-the-user-history-helps/) |
| `23-personalized-search` | History can hide what the query asked for | [when-personalization-hurts](23-personalized-search/when-personalization-hurts/) |
| `24-search-measurement` | A failed query can be a recovered session | [when-the-click-is-a-query](24-search-measurement/when-the-click-is-a-query/) |
| `24-search-measurement` | Zero results is a coverage metric with a revenue shape | [when-the-zero-result-rate-matters](24-search-measurement/when-the-zero-result-rate-matters/) |
| `25-frequency-capping` | The cap is a budget allocation, not a setting | [when-the-cap-bites](25-frequency-capping/when-the-cap-bites/) |
| `25-frequency-capping` | More impressions buy fewer clicks once fatigue sets in | [when-fatigue-hits](25-frequency-capping/when-fatigue-hits/) |
| `26-creative-selection` | Logged CTR mixes quality with wear | [when-the-creative-is-stale](26-creative-selection/when-the-creative-is-stale/) |
| `26-creative-selection` | Context is a feature of creative selection | [when-the-creative-context-changes](26-creative-selection/when-the-creative-context-changes/) |
| `27-bid-strategy` | The target CPA is a walk-away line | [when-the-target-cpa-binds](27-bid-strategy/when-the-target-cpa-binds/) |
| `27-bid-strategy` | The cap is a risk dial, not a price | [when-the-bid-is-capped](27-bid-strategy/when-the-bid-is-capped/) |
| `28-auction-revenue` | First price pays more only when bidders stay honest | [when-first-price-pays-more](28-auction-revenue/when-first-price-pays-more/) |
| `28-auction-revenue` | The reserve sits on the demand curve | [when-the-reserve-moves-revenue](28-auction-revenue/when-the-reserve-moves-revenue/) |
| `29-rtb-pipeline` | Latency is a bidder's cost of entry | [when-the-bidder-is-slow](29-rtb-pipeline/when-the-bidder-is-slow/) |
| `29-rtb-pipeline` | Every timeout is a slot that sells nothing | [when-the-exchange-times-out](29-rtb-pipeline/when-the-exchange-times-out/) |
| `30-ads-measurement` | The measurement model decides which channel gets the budget | [when-attribution-overcounts](30-ads-measurement/when-attribution-overcounts/) |
| `30-ads-measurement` | Zero lift is the null result measurement exists to find | [when-the-incrementality-is-zero](30-ads-measurement/when-the-incrementality-is-zero/) |

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
[mission 01's corpus stage](../../missions/01-language-model-agent/00-corpus/), the training engineering from
[mission 01's pretraining stage](../01-language-model-agent/02-pretrain/) — gradient accumulation, mixed
precision, resumable checkpoints — the serving concerns from
[mission 01's serving stage](../../missions/01-language-model-agent/05-serve/), and the evaluation discipline
from [mission 01's evaluation stage](../../missions/01-language-model-agent/07-eval/),
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
