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
[open-source line behind personalized discovery](lineage.md)
traces each predecessor and the tradeoff it made.

## Stages

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`00-interactions`](shared/00-interactions/) | Public interaction dataset, cleaned, split **by time** — a random split leaks the future | mission 01 · corpus | implementation present; run pending |
| [`01-content-understanding`](shared/01-content-understanding/) | VLM labelling of items into taxonomy + embeddings; cold-item coverage measured | mission 01 · agent harness | verified synthetic mechanism run; mission outcome pending |
| [`02-recall`](shared/02-recall/) | Multi-queue: two-tower, lexical, i2i, fresh; union and dedup; recall@1000 vs exhaustive | new to this mission | implementation present; run pending |
| [`03-pre-rank`](shared/03-pre-rank/) | Lightweight scorer, 1000→100, with pre-rank/fine-rank agreement analysis | new to this mission | implementation present; run pending |
| [`04-fine-rank`](shared/04-fine-rank/) | Multi-objective model: click, dwell, completion, satisfaction | new to this mission | implementation present; run pending |
| [`05-value-tree`](shared/05-value-tree/) | Objective combination, calibration, explicit user-value/revenue trade rates | new to this mission | implementation present; run pending |
| [`06-mixing`](shared/06-mixing/) | Slate assembly by beam search; diversity; ad interleaving with displacement cost | new to this mission | verified synthetic mechanism run; mission outcome pending |
| [`07-rule-engine`](shared/07-rule-engine/) | Declarative constraints, auditable decisions, policy-timescale changes | mission 01 · eval gates | verified synthetic mechanism run; mission outcome pending |
| [`08-serving`](shared/08-serving/) | Two-stage serving inside p95 300ms; ANN index; measured | mission 01 · serving | verified synthetic mechanism run; mission outcome pending |
| [`09-report`](shared/09-report/) | Outcome vs both baselines and all guardrails, with failure cases | mission 01 · eval | verified evaluator run; outcome cannot determine |

### The search track (stages 10-13)

Search is the same decision loop with an explicit query. The four stages
below take the query from raw string to a ranked, evaluated result — the
search analogue of recommendation's recall-to-report funnel.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`10-query-understanding`](search/10-query-understanding/) | Tokenize, normalize, and classify the query; the key space retrieval must serve | new to this mission | verified mechanism run |
| [`11-search-retrieval`](search/11-search-retrieval/) | BM25 lexical index; the vocabulary-mismatch gap dense retrieval must close | new to this mission | verified mechanism run |
| [`12-search-ranking`](search/12-search-ranking/) | Pointwise vs pairwise ranking over the candidate set; NDCG as arbiter | new to this mission | verified mechanism run |
| [`13-search-evaluation`](search/13-search-evaluation/) | NDCG@k and MRR; the metric blind spots that force the declared choice | mission 01 · eval | verified mechanism run |

### The ads track (stages 14-18)

Ads insert a paid item into either surface, and every ad displaces an
organic result. The five stages below run the economics: allocation,
revenue ranking, calibration, delivery, and the displacement trade.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`14-ad-auction`](ads/14-ad-auction/) | Second-price auction; truthful bidding as the dominant strategy | new to this mission | verified mechanism run |
| [`15-ecpm-ranking`](ads/15-ecpm-ranking/) | Bid x pCTR revenue ranking; the lower bid that wins | new to this mission | verified mechanism run |
| [`16-ctr-calibration`](ads/16-ctr-calibration/) | pCTR calibration (ECE) and the correction that makes the estimate honest | new to this mission | verified mechanism run |
| [`17-budget-pacing`](ads/17-budget-pacing/) | Budget delivery under a per-hour cap; the feedback signal | new to this mission | verified mechanism run |
| [`18-ad-externality`](ads/18-ad-externality/) | The displacement trade; scarcity amplifies the externality | mission 02 · value tree | verified mechanism run |

### The advanced search track (stages 19-24)

The four-stage search track (10-13) ran the query from raw string to
ranked result. The six stages below deepen it to production depth:
repair the query, add a meaning-based index, fuse the matchers, rerank,
personalize, and measure the queries that return nothing.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`19-query-expansion`](search/19-query-expansion/) | Query correction as retrieval pre-processing; recall recovered | new to this mission | verified mechanism run |
| [`20-dense-retrieval`](search/20-dense-retrieval/) | Two-tower cosine retrieval; the meaning-based index | new to this mission | verified mechanism run |
| [`21-hybrid-fusion`](search/21-hybrid-fusion/) | Reciprocal rank fusion of lexical and dense sets; the union kept | new to this mission | verified mechanism run |
| [`22-reranking`](search/22-reranking/) | Second ranker over the top-k; the latency-budget split | new to this mission | verified mechanism run |
| [`23-personalized-search`](search/23-personalized-search/) | Relevance plus user affinity; the query with a user attached | new to this mission | verified mechanism run |
| [`24-search-measurement`](search/24-search-measurement/) | Zero-result rate and its causes; the coverage signal | new to this mission | verified mechanism run |

### The advanced ads track (stages 25-30)

The five-stage ads track (14-18) ran the economics of a paid slot. The
six stages below add the delivery and measurement depth: cap
frequency, choose the creative, derive the bid, compare auction rules,
fit the 100ms deadline, and measure what the ad actually changed.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`25-frequency-capping`](ads/25-frequency-capping/) | The exposure cap; CTR decay makes it a value decision | new to this mission | verified mechanism run |
| [`26-creative-selection`](ads/26-creative-selection/) | Per-context creative choice; the creative feeds eCPM | new to this mission | verified mechanism run |
| [`27-bid-strategy`](ads/27-bid-strategy/) | Target-CPA bid as value times conversion; the walk-away line | new to this mission | verified mechanism run |
| [`28-auction-revenue`](ads/28-auction-revenue/) | First versus second price; the rule moves revenue | new to this mission | verified mechanism run |
| [`29-rtb-pipeline`](ads/29-rtb-pipeline/) | The 100ms real-time bid; latency as a selection mechanism | new to this mission | verified mechanism run |
| [`30-ads-measurement`](ads/30-ads-measurement/) | Incrementality against a control; the ad's actual effect | new to this mission | verified mechanism run |

### The frontier recommendation track (stages 31-34)

The core recommendation stages (00-09) ran the funnel end to end. The
four stages below revisit it with the tools that changed after it was
built: the LLM as a listwise ranker, preference optimization instead of
labels, content vectors for cold start, and the slate as the unit of
evaluation.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`31-llm-ranking`](recommendation/31-llm-ranking/) | LLM listwise reorder over the top of a cascade; token budget as recall boundary | new to this mission | verified mechanism run |
| [`32-recommendation-rlhf`](recommendation/32-recommendation-rlhf/) | Pairwise preference optimization; the Bradley-Terry objective | new to this mission | verified mechanism run |
| [`33-multimodal-recall`](recommendation/33-multimodal-recall/) | VLM content vectors as the cold-start bridge; per-modality reachability | new to this mission | verified mechanism run |
| [`34-slate-vs-item-evaluation`](recommendation/34-slate-vs-item-evaluation/) | Slate value versus item-score sum; the metric that sees the page | new to this mission | verified mechanism run |

### The frontier search track (stages 35-37)

The search stages (10-13, 19-24) ran the query through the funnel. The
three stages below change the input side: retrieval by generation
instead of index, a query that carries a session, and an LLM that parses
the raw string into the key space.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`35-generative-retrieval`](search/35-generative-retrieval/) | Doc-ID beam decode; retrieval as a decode with a recall curve | new to this mission | verified mechanism run |
| [`36-conversational-search`](search/36-conversational-search/) | Session context as the resolution signal for follow-up turns | new to this mission | verified mechanism run |
| [`37-llm-query-understanding`](search/37-llm-query-understanding/) | LLM intent-slot parsing with a confidence floor per slot | new to this mission | verified mechanism run |

### The frontier ads track (stages 38-42)

The ads stages (14-18, 25-30) ran the auction and the measurement. The
five stages below take the ads decision to the frontier: within-user
experiments, the first-price transition, privacy-safe attribution,
generated creative, and the marketplace lever behind all of them.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`38-interleaving-experiments`](ads/38-interleaving-experiments/) | Blended-list ranking comparison; credits with a tie rule | new to this mission | verified mechanism run |
| [`39-first-price-transition`](ads/39-first-price-transition/) | Shading under first price; the bid as an estimation problem | new to this mission | verified mechanism run |
| [`40-privacy-safe-attribution`](ads/40-privacy-safe-attribution/) | DP-noised channel counts; epsilon as the decision-accuracy dial | new to this mission | verified mechanism run |
| [`41-llm-creative-generation`](ads/41-llm-creative-generation/) | Generate-then-select creative; diversity and calibration guards | new to this mission | verified mechanism run |
| [`42-marketplace-economics`](ads/42-marketplace-economics/) | Take rate and ad load as marketplace decisions with a peak | new to this mission | verified mechanism run |


### The operations track (stages 43-55)

The frontier tracks ran the three surfaces to the edge of the models.
The thirteen stages below run the system around them: the pipeline that
keeps training and serving consistent, the feedback that entrenches what
the ranker shows, the monitoring that catches the world moving, the
machines and budgets that serve the query, the user who has no trail
yet, the explanation the user can check, the exposure the page
allocates, and the advertiser and user economics that decide whether the
whole system pays.

| Stage | Deliverable | Layer | Status |
|---|---|---|---|
| [`43-feature-store`](shared/43-feature-store/) | The feature computed once and served identically to training and serving | new to this mission | verified mechanism + audit run |
| [`44-training-serving-consistency`](shared/44-training-serving-consistency/) | Logged price versus live price; the skew as a pipeline property | new to this mission | verified mechanism + audit run |
| [`45-feedback-loops`](shared/45-feedback-loops/) | The model's output as its next training data; exposure entrenches | new to this mission | verified mechanism + audit run |
| [`46-retraining-and-staleness`](shared/46-retraining-and-staleness/) | Snapshot age as the retraining trigger; the measured gap | new to this mission | verified mechanism + audit run |
| [`47-monitoring-and-drift`](shared/47-monitoring-and-drift/) | The prediction-observation gap as the online signal | new to this mission | verified mechanism + audit run |
| [`48-realtime-user-state`](shared/48-realtime-user-state/) | The session as a feature the batch model cannot see | new to this mission | verified mechanism run |
| [`49-throughput-and-capacity`](shared/49-throughput-and-capacity/) | Capacity as throughput times deadline, not times average latency | new to this mission | verified mechanism run |
| [`50-cost-per-query`](shared/50-cost-per-query/) | The cascade's arithmetic with a price tag per query | new to this mission | verified mechanism run |
| [`51-new-user-experience`](shared/51-new-user-experience/) | The first page decided before personalization can see the user | new to this mission | verified mechanism run |
| [`52-trust-and-explainability`](shared/52-trust-and-explainability/) | The explanation the user can actually check | new to this mission | verified mechanism run |
| [`53-fairness-and-allocation`](shared/53-fairness-and-allocation/) | Exposure as a budget the ranker allocates, at a measured price | new to this mission | verified mechanism run |
| [`54-online-experiments`](shared/54-online-experiments/) | Whether a shipped change helped, read through a validity gate | new to this mission | verified mechanism run |
| [`54-advertiser-roas`](ads/54-advertiser-roas/) | The advertiser's return as the platform's revenue | new to this mission | verified mechanism run |
| [`55-ltv-and-cac`](shared/55-ltv-and-cac/) | The user lifecycle that decides which growth is real growth | new to this mission | verified mechanism run |



## Where each stage leaves the path

A stage states a decision; these deep-dive chapters answer the decisions
the main path asserts without showing, mission-01 style — each returns an
artifact or a measurement the next stage consumes.

| At this stage | You need to decide | So read |
|---|---|---|
| `00-interactions` | The filter that catches users it did not aim at | [the-eligibility-cascade](shared/00-interactions/the-eligibility-cascade/) |
| `00-interactions` | The 99.1% leak: what the wrong split actually buys | [when-the-split-leaks](shared/00-interactions/when-the-split-leaks/) |
| `00-interactions` | The absence is a signal | [when-the-absence-is-a-signal](shared/00-interactions/when-the-absence-is-a-signal/) |
| `01-content-understanding` | The behavioural floor the threshold cannot touch | [the-63-percent-that-never-moves](shared/01-content-understanding/the-63-percent-that-never-moves/) |
| `01-content-understanding` | The confidence threshold: precision for the head, or reach for the tail? | [when-the-threshold-rescues-the-tail](shared/01-content-understanding/when-the-threshold-rescues-the-tail/) |
| `01-content-understanding` | The label the threshold cannot trust | [when-the-label-is-noisy](shared/01-content-understanding/when-the-label-is-noisy/) |
| `02-recall` | Recall bought back at a measured latency cost | [the-price-of-approximate](shared/02-recall/the-price-of-approximate/) |
| `02-recall` | The queue you disable is the target you lose | [when-you-lose-a-queue](shared/02-recall/when-you-lose-a-queue/) |
| `02-recall` | The tail that the index forgets | [when-the-tail-goes-cold](shared/02-recall/when-the-tail-goes-cold/) |
| `03-pre-rank` | When does the cheap cut fail? | [when-the-cheap-cut-fails](shared/03-pre-rank/when-the-cheap-cut-fails/) |
| `03-pre-rank` | The zero that is structural, not a tuning miss | [when-the-long-tail-is-invisible](shared/03-pre-rank/when-the-long-tail-is-invisible/) |
| `03-pre-rank` | The cheap score that flips the cut | [when-the-cheap-score-lies](shared/03-pre-rank/when-the-cheap-score-lies/) |
| `04-fine-rank` | Why ECE is a gate, not a polish step | [the-calibration-that-decides](shared/04-fine-rank/the-calibration-that-decides/) |
| `04-fine-rank` | When does the shared model hurt an objective? | [when-sharing-hurts](shared/04-fine-rank/when-sharing-hurts/) |
| `04-fine-rank` | The model that learned yesterday | [when-the-model-is-stale](shared/04-fine-rank/when-the-model-is-stale/) |
| `05-value-tree` | The same strategy, different calibration, different slate | [the-calibration-break](shared/05-value-tree/the-calibration-break/) |
| `05-value-tree` | The weight IS the strategy | [when-the-weight-moves](shared/05-value-tree/when-the-weight-moves/) |
| `05-value-tree` | The dislike that flips the weight | [when-the-user-rejects](shared/05-value-tree/when-the-user-rejects/) |
| `06-mixing` | A narrow beam finding the optimum is not proof a beam is enough | [when-the-beam-is-wide-enough](shared/06-mixing/when-the-beam-is-wide-enough/) |
| `06-mixing` | What does a mixing weight actually trade off? | [when-the-trade-weight-moves](shared/06-mixing/when-the-trade-weight-moves/) |
| `06-mixing` | The diverse slate that underperforms | [when-diversity-hurts](shared/06-mixing/when-diversity-hurts/) |
| `07-rule-engine` | A rule engine's failure mode is interaction, not any single rule | [the-empty-set-was-two-rules](shared/07-rule-engine/the-empty-set-was-two-rules/) |
| `07-rule-engine` | When does the rule engine return an empty set? | [when-the-rules-collide](shared/07-rule-engine/when-the-rules-collide/) |
| `07-rule-engine` | The rule nobody tested | [when-the-rule-is-a-typo](shared/07-rule-engine/when-the-rule-is-a-typo/) |
| `08-serving` | Means add for the serial path; tail percentiles do not | [when-p95s-do-not-add](shared/08-serving/when-p95s-do-not-add/) |
| `08-serving` | What does the pre-rank cut buy, and when does it stop paying? | [when-the-cut-bites](shared/08-serving/when-the-cut-bites/) |
| `08-serving` | The cache that misses together | [when-the-cache-goes-cold](shared/08-serving/when-the-cache-goes-cold/) |
| `09-report` | A headline win that still loses, seed by seed | [the-variance-that-decides](shared/09-report/the-variance-that-decides/) |
| `09-report` | A headline win that is still NOT MET | [when-the-guardrail-vetoes](shared/09-report/when-the-guardrail-vetoes/) |
| `09-report` | The baseline that moved | [when-the-baseline-moves](shared/09-report/when-the-baseline-moves/) |
| `10-query-understanding` | Where normalization stops and correction must begin | [when-the-query-is-misspelled](search/10-query-understanding/when-the-query-is-misspelled/) |
| `10-query-understanding` | One word, many intents | [when-the-query-is-short](search/10-query-understanding/when-the-query-is-short/) |
| `11-search-retrieval` | The document that means the same but scores less | [when-the-synonym-is-invisible](search/11-search-retrieval/when-the-synonym-is-invisible/) |
| `11-search-retrieval` | The embedding that sees the synonym | [when-the-dense-path-exists](search/11-search-retrieval/when-the-dense-path-exists/) |
| `12-search-ranking` | The label that carries the position's bias | [when-the-label-is-a-click](search/12-search-ranking/when-the-label-is-a-click/) |
| `12-search-ranking` | Where the formulation choice actually matters | [when-the-list-is-longer](search/12-search-ranking/when-the-list-is-longer/) |
| `13-search-evaluation` | The metric chooses the winner | [when-mrr-and-ndcg-disagree](search/13-search-evaluation/when-mrr-and-ndcg-disagree/) |
| `13-search-evaluation` | NDCG@1 is a different claim than NDCG@5 | [when-the-k-is-small](search/13-search-evaluation/when-the-k-is-small/) |
| `14-ad-auction` | The floor that can also kill the sale | [when-the-reserve-price-bites](ads/14-ad-auction/when-the-reserve-price-bites/) |
| `14-ad-auction` | The dominant strategy is the honest one | [when-truthful-bidding-is-optimal](ads/14-ad-auction/when-truthful-bidding-is-optimal/) |
| `15-ecpm-ranking` | The knife-edge the click estimate sits on | [when-pctr-moves-the-rank](ads/15-ecpm-ranking/when-pctr-moves-the-rank/) |
| `15-ecpm-ranking` | The reserve and the ranking are one decision | [when-the-reserve-interacts](ads/15-ecpm-ranking/when-the-reserve-interacts/) |
| `16-ctr-calibration` | The fix that makes the estimate honest | [when-the-correction-is-needed](ads/16-ctr-calibration/when-the-correction-is-needed/) |
| `16-ctr-calibration` | Perfect order, wrong values | [when-calibration-and-ranking-conflict](ads/16-ctr-calibration/when-calibration-and-ranking-conflict/) |
| `17-budget-pacing` | The cap that binds when demand spikes | [when-delivery-varies](ads/17-budget-pacing/when-delivery-varies/) |
| `17-budget-pacing` | Pacing cannot create a budget | [when-the-budget-is-tiny](ads/17-budget-pacing/when-the-budget-is-tiny/) |
| `18-ad-externality` | Scarcity amplifies the externality | [when-the-slot-is-scarce](ads/18-ad-externality/when-the-slot-is-scarce/) |
| `18-ad-externality` | The externality flips sign when the ad is relevant | [when-the-ad-is-relevant](ads/18-ad-externality/when-the-ad-is-relevant/) |
| `19-query-expansion` | The correction recovers what the raw query could not | [when-the-correction-helps](search/19-query-expansion/when-the-correction-helps/) |
| `19-query-expansion` | Expansion trades precision for recall | [when-expansion-hurts](search/19-query-expansion/when-expansion-hurts/) |
| `20-dense-retrieval` | Approximate is the only feasible index at scale | [when-the-index-is-ann](search/20-dense-retrieval/when-the-index-is-ann/) |
| `20-dense-retrieval` | The item without a vector is unreachable | [when-the-embedding-is-stale](search/20-dense-retrieval/when-the-embedding-is-stale/) |
| `21-hybrid-fusion` | The fusion weight is a trust decision | [when-the-fusion-weight-moves](search/21-hybrid-fusion/when-the-fusion-weight-moves/) |
| `21-hybrid-fusion` | The hybrid degrades into whoever is alive | [when-one-set-is-empty](search/21-hybrid-fusion/when-one-set-is-empty/) |
| `22-reranking` | The cutoff decides what the reranker can fix | [when-the-rerank-budget-is-tight](search/22-reranking/when-the-rerank-budget-is-tight/) |
| `22-reranking` | Disagreement is the reranker's job and its risk | [when-the-reranker-disagrees](search/22-reranking/when-the-reranker-disagrees/) |
| `23-personalized-search` | History is a prior over the query | [when-the-user-history-helps](search/23-personalized-search/when-the-user-history-helps/) |
| `23-personalized-search` | History can hide what the query asked for | [when-personalization-hurts](search/23-personalized-search/when-personalization-hurts/) |
| `24-search-measurement` | A failed query can be a recovered session | [when-the-click-is-a-query](search/24-search-measurement/when-the-click-is-a-query/) |
| `24-search-measurement` | Zero results is a coverage metric with a revenue shape | [when-the-zero-result-rate-matters](search/24-search-measurement/when-the-zero-result-rate-matters/) |
| `25-frequency-capping` | The cap is a budget allocation, not a setting | [when-the-cap-bites](ads/25-frequency-capping/when-the-cap-bites/) |
| `25-frequency-capping` | More impressions buy fewer clicks once fatigue sets in | [when-fatigue-hits](ads/25-frequency-capping/when-fatigue-hits/) |
| `26-creative-selection` | Logged CTR mixes quality with wear | [when-the-creative-is-stale](ads/26-creative-selection/when-the-creative-is-stale/) |
| `26-creative-selection` | Context is a feature of creative selection | [when-the-creative-context-changes](ads/26-creative-selection/when-the-creative-context-changes/) |
| `27-bid-strategy` | The target CPA is a walk-away line | [when-the-target-cpa-binds](ads/27-bid-strategy/when-the-target-cpa-binds/) |
| `27-bid-strategy` | The cap is a risk dial, not a price | [when-the-bid-is-capped](ads/27-bid-strategy/when-the-bid-is-capped/) |
| `28-auction-revenue` | First price pays more only when bidders stay honest | [when-first-price-pays-more](ads/28-auction-revenue/when-first-price-pays-more/) |
| `28-auction-revenue` | The reserve sits on the demand curve | [when-the-reserve-moves-revenue](ads/28-auction-revenue/when-the-reserve-moves-revenue/) |
| `29-rtb-pipeline` | Latency is a bidder's cost of entry | [when-the-bidder-is-slow](ads/29-rtb-pipeline/when-the-bidder-is-slow/) |
| `29-rtb-pipeline` | Every timeout is a slot that sells nothing | [when-the-exchange-times-out](ads/29-rtb-pipeline/when-the-exchange-times-out/) |
| `30-ads-measurement` | The measurement model decides which channel gets the budget | [when-attribution-overcounts](ads/30-ads-measurement/when-attribution-overcounts/) |
| `30-ads-measurement` | Zero lift is the null result measurement exists to find | [when-the-incrementality-is-zero](ads/30-ads-measurement/when-the-incrementality-is-zero/) |
| `31-llm-ranking` | The LLM disagrees with the pointwise order where the user looks | [when-the-llm-disagrees](recommendation/31-llm-ranking/when-the-llm-disagrees/) |
| `31-llm-ranking` | The prompt token budget is the ranker's recall boundary | [when-the-prompt-token-budget-binds](recommendation/31-llm-ranking/when-the-prompt-token-budget-binds/) |
| `32-recommendation-rlhf` | The flipped label sets a loss floor the clean pairs cannot remove | [when-the-preference-is-noisy](recommendation/32-recommendation-rlhf/when-the-preference-is-noisy/) |
| `32-recommendation-rlhf` | The reward is gamed by the policy that maximizes it | [when-the-reward-is-gamed](recommendation/32-recommendation-rlhf/when-the-reward-is-gamed/) |
| `33-multimodal-recall` | The cold image is reachable through one modality only | [when-the-image-is-cold](recommendation/33-multimodal-recall/when-the-image-is-cold/) |
| `33-multimodal-recall` | The modality mismatch biases recall toward text-rich items | [when-the-modality-mismatch](recommendation/33-multimodal-recall/when-the-modality-mismatch/) |
| `34-slate-vs-item-evaluation` | The diverse slate trades a top item for coverage | [when-the-slate-is-diverse](recommendation/34-slate-vs-item-evaluation/when-the-slate-is-diverse/) |
| `34-slate-vs-item-evaluation` | The item-level metric ties slates the user experiences differently | [when-the-metric-misses-diversity](recommendation/34-slate-vs-item-evaluation/when-the-metric-misses-diversity/) |
| `35-generative-retrieval` | Decode accuracy falls as the ID space grows | [when-the-id-space-grows](search/35-generative-retrieval/when-the-id-space-grows/) |
| `35-generative-retrieval` | The generator hallucinates an ID that does not exist | [when-the-generator-hallucinates](search/35-generative-retrieval/when-the-generator-hallucinates/) |
| `36-conversational-search` | The topic shifts and the old context goes stale | [when-the-topic-shifts](search/36-conversational-search/when-the-topic-shifts/) |
| `36-conversational-search` | The anaphora is ambiguous between two referents | [when-the-anaphora-is-ambiguous](search/36-conversational-search/when-the-anaphora-is-ambiguous/) |
| `37-llm-query-understanding` | The empty slot makes retrieval decide | [when-the-slot-is-empty](search/37-llm-query-understanding/when-the-slot-is-empty/) |
| `37-llm-query-understanding` | The LLM invents a slot and silently shrinks recall | [when-the-llm-over-parses](search/37-llm-query-understanding/when-the-llm-over-parses/) |
| `38-interleaving-experiments` | Shared documents blur the credit without a tie rule | [when-the-credit-is-unbalanced](ads/38-interleaving-experiments/when-the-credit-is-unbalanced/) |
| `38-interleaving-experiments` | The traffic is too tiny for a between-user A/B | [when-the-traffic-is-tiny](ads/38-interleaving-experiments/when-the-traffic-is-tiny/) |
| `39-first-price-transition` | The shading error is a direct cost on both sides | [when-the-shading-is-wrong](ads/39-first-price-transition/when-the-shading-is-wrong/) |
| `39-first-price-transition` | Revenue falls as bidders learn to shade | [when-the-market-adjusts](ads/39-first-price-transition/when-the-market-adjusts/) |
| `40-privacy-safe-attribution` | The noise collapses the order at low epsilon | [when-the-noise-is-too-high](ads/40-privacy-safe-attribution/when-the-noise-is-too-high/) |
| `40-privacy-safe-attribution` | Every extra report dilutes the shared privacy budget | [when-the-budget-splits](ads/40-privacy-safe-attribution/when-the-budget-splits/) |
| `41-llm-creative-generation` | Generation collapses and leaves nothing to score | [when-the-generated-creative-is-identical](ads/41-llm-creative-generation/when-the-generated-creative-is-identical/) |
| `41-llm-creative-generation` | The surface score ships the creative that converts worst | [when-the-score-is-on-surface](ads/41-llm-creative-generation/when-the-score-is-on-surface/) |
| `42-marketplace-economics` | The take rate is too high and the marketplace collapses | [when-the-take-rate-is-too-high](ads/42-marketplace-economics/when-the-take-rate-is-too-high/) |
| `42-marketplace-economics` | The marginal ad stops paying for its displacement | [when-the-ad-load-moves](ads/42-marketplace-economics/when-the-ad-load-moves/) |
| `43-feature-store` | The feature diverges and the ranker reorders on a value the model never saw | [when-the-feature-diverges](shared/43-feature-store/when-the-feature-diverges/) |
| `43-feature-store` | A missing feature default is a silent ranking decision | [when-the-feature-is-missing](shared/43-feature-store/when-the-feature-is-missing/) |
| `43-feature-store` | The store freezes a value; the refresh decides how stale it gets | [when-the-online-value-moves](shared/43-feature-store/when-the-online-value-moves/) |
| `44-training-serving-consistency` | The label that arrives late biases the training set | [when-the-label-arrives-late](shared/44-training-serving-consistency/when-the-label-arrives-late/) |
| `44-training-serving-consistency` | The online feature that lags serves a world that ended | [when-the-online-feature-lags](shared/44-training-serving-consistency/when-the-online-feature-lags/) |
| `44-training-serving-consistency` | The join that looks ahead trains the model on its own outcome | [when-the-join-looks-ahead](shared/44-training-serving-consistency/when-the-join-looks-ahead/) |
| `45-feedback-loops` | The loop is the last to notice the world changed | [when-popularity-collapses](shared/45-feedback-loops/when-popularity-collapses/) |
| `45-feedback-loops` | The filter bubble closes from the inside | [when-the-filter-bubble-closes](shared/45-feedback-loops/when-the-filter-bubble-closes/) |
| `45-feedback-loops` | The log measures quality under the policy, not quality | [when-the-policy-borrows-luck](shared/45-feedback-loops/when-the-policy-borrows-luck/) |
| `46-retraining-and-staleness` | The retrain that flips the metric offline can lose online | [when-retraining-flips-the-metric](shared/46-retraining-and-staleness/when-retraining-flips-the-metric/) |
| `46-retraining-and-staleness` | The embedding expires and recall dies with it | [when-the-embedding-expires](shared/46-retraining-and-staleness/when-the-embedding-expires/) |
| `46-retraining-and-staleness` | A calendar retrain misses the spike; an error trigger does not | [when-the-peak-hits](shared/46-retraining-and-staleness/when-the-peak-hits/) |
| `47-monitoring-and-drift` | A threshold tight enough to catch a break fires on noise | [when-the-alert-is-noisy](shared/47-monitoring-and-drift/when-the-alert-is-noisy/) |
| `47-monitoring-and-drift` | The drift is silent in the eval and loud in the gap | [when-the-drift-is-silent](shared/47-monitoring-and-drift/when-the-drift-is-silent/) |
| `47-monitoring-and-drift` | The aggregate hides the slice; the slice's own noise hides the fix | [when-the-slice-hides](shared/47-monitoring-and-drift/when-the-slice-hides/) |
| `48-realtime-user-state` | Realtime is too expensive once every feature is on the critical path | [when-realtime-is-too-expensive](shared/48-realtime-user-state/when-realtime-is-too-expensive/) |
| `48-realtime-user-state` | The session boost decays and the batch order wins back | [when-the-session-state-moves](shared/48-realtime-user-state/when-the-session-state-moves/) |
| `49-throughput-and-capacity` | The peak is a capacity decision, not a load average | [when-the-peak-arrives](shared/49-throughput-and-capacity/when-the-peak-arrives/) |
| `49-throughput-and-capacity` | Sizing to the mean is sizing to a fiction | [when-the-tail-costs](shared/49-throughput-and-capacity/when-the-tail-costs/) |
| `50-cost-per-query` | The cache pays when the hit rate is a cost decision | [when-the-cache-pays](shared/50-cost-per-query/when-the-cache-pays/) |
| `50-cost-per-query` | The model is too big when the last point of quality doubles the bill | [when-the-model-is-too-big](shared/50-cost-per-query/when-the-model-is-too-big/) |
| `51-new-user-experience` | A confident prior reads as a misread | [when-personalization-scares](shared/51-new-user-experience/when-personalization-scares/) |
| `51-new-user-experience` | The onboarding prior is a bet on an answer the user may not mean | [when-the-user-is-new](shared/51-new-user-experience/when-the-user-is-new/) |
| `52-trust-and-explainability` | The attribution that explains the score tells a story the score did not | [when-the-explanation-is-wrong](shared/52-trust-and-explainability/when-the-explanation-is-wrong/) |
| `52-trust-and-explainability` | A false explanation burns trust faster than a missing one | [when-trust-erodes](shared/52-trust-and-explainability/when-trust-erodes/) |
| `53-fairness-and-allocation` | The floor has a price and the price is a curve | [when-the-constraint-bites](shared/53-fairness-and-allocation/when-the-constraint-bites/) |
| `53-fairness-and-allocation` | The label carries the position it was collected in | [when-the-policy-is-biased](shared/53-fairness-and-allocation/when-the-policy-is-biased/) |
| `54-online-experiments` | The split check fires before the outcome test has power | [when-the-split-lies](shared/54-online-experiments/when-the-split-lies/) |
| `54-online-experiments` | The user who sits in both arms biases the estimate | [when-the-user-crosses-groups](shared/54-online-experiments/when-the-user-crosses-groups/) |
| `54-online-experiments` | The market leaks across the groups; the block unit prices it | [when-the-traffic-is-two-sided](shared/54-online-experiments/when-the-traffic-is-two-sided/) |
| `54-advertiser-roas` | The marginal dollar buys less every time | [when-roas-collapses](ads/54-advertiser-roas/when-roas-collapses/) |
| `54-advertiser-roas` | The advertiser's exit is the platform's loss | [when-the-budget-moves](ads/54-advertiser-roas/when-the-budget-moves/) |
| `55-ltv-and-cac` | The user who costs more than they return is a liability at any volume | [when-cac-exceeds-ltv](shared/55-ltv-and-cac/when-cac-exceeds-ltv/) |
| `55-ltv-and-cac` | The user who stops leaving is worth more than the user who stops coming | [when-retention-flattens](shared/55-ltv-and-cac/when-retention-flattens/) |

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
[mission 01's corpus stage](../01-language-model/00-corpus/), the training engineering from
[mission 01's pretraining stage](../01-language-model/02-pretrain/) — gradient accumulation, mixed
precision, resumable checkpoints — the serving concerns from
[mission 01's serving stage](../01-language-model/05-serve/), and the evaluation discipline
from [mission 01's evaluation stage](../01-language-model/07-eval/),
where harness disclosure and seed variance already live.

New capabilities live inside this mission until a **second** mission needs them,
per the gate in [`standards/mission-contract.md`](../reference/standards/mission-contract.md).
`perceive-understand` is the likely first graduate, since multimodal content
intelligence would reuse it directly.

## Sequencing

Mission 01 finishes before this one starts building. That ordering is
deliberate: this mission's value is demonstrating the platform layers are
reusable, and that claim is worthless while those layers are still being built.
What exists now is the contract and the architecture — which is exactly what
[`mission.yaml`](mission.yaml) requires before any code is written.
