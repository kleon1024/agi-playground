---
level: reference
---

# The depth audit

The curriculum's job is not to be wide. It is to make a reader able to
*operate* a production system — which means the curriculum has to show the
failure modes that production systems actually hit, and the fix that each one
exists to serve. A "deep detail" in any real system is almost always a
solution to a failure mode: sparse labels, delayed feedback, cold start, a
leaky split, a cascade that disagrees with its own ranker, dirty training
data. When a chapter only names the mechanism and skips the failure mode, the
reader learns a vocabulary, not a system.

This document is the standing audit program for that depth. It is a queue,
not a one-time pass: sections are audited one at a time, in the order below,
and each audit must satisfy the contract before it is marked done.

## The audit contract

An audited section must, for each stage it covers, do all of the following:

1. **Name the failure mode before the fix.** The chapter opens with the
   operational symptom (a metric that drifts, a label that lies, a rank that
   disagrees with the page) and the cost of ignoring it.
2. **Show how you find the case.** Distribution checks, per-stage offline
   consistency, sampling, stratification, case triage — the reader learns
   where the failure shows up, not just what it is.
3. **Show the fix and what it trades.** Every fix has a cost: more labels vs
   freshness, calibration vs ranking, exploration vs exploitation. The chapter
   measures the trade with a run.
4. **Cover the whole production loop, not the model alone.** For every stage
   that touches them: model detail, sample construction, data pipeline,
   feature engineering, API and engineering implementation, product alignment,
   and the cross-team handoff (who owns the label, who owns the cut, who owns
   the traffic).
5. **Never write from memory.** Research and industry practice must be
   integrated, attributed, and dated. If a claim is not in a `runs/` record or
   a cited source, it does not go in. Estimates and "typical" values are
   failures here.
6. **Serve the interview goal.** The section must leave the reader able to
   answer the operational version of the question: what breaks, how do you
   find it, what do you do, how do you know it worked.

## The failure-mode canvas

Every domain gets a canvas that names its failure modes, the pipeline stage
that owns each one, and the technique class that addresses it. The canvas is
not the lesson; it is the checklist an auditor runs against the section.

| Domain | Failure mode | Stage that owns it | Technique class |
|---|---|---|---|
| Recommendation | Sparse labels | sample construction, label generation | entire-space funnel, multi-task, label smoothing |
| Recommendation | Delayed feedback | label window, freshness | windowing, fake-negative correction, survival-style weighting |
| Recommendation | Exposure bias | data collection, logging | IPS, propensity estimation, exploration traffic |
| Recommendation | Cold start | retrieval, features | content embeddings, warm-start priors |
| Recommendation | Heavy-tail targets | objective, loss | log/quantile objectives, gradient balancing |
| Recommendation | Funnel inconsistency | model family, serving | probability-constrained heads, stage-consistent training |
| Recommendation | Cascade inconsistency | pre-rank, rank, serving | distillation that preserves top-k, cut-aware training |
| Any ranking | Sample split leakage | evaluation | user/query-cluster splits, as-of joins |
| Any ranking | A/B traffic split | experimentation | SRM checks, unit of randomization, carryover |
| Any ranking | Offline/online divergence | evaluation, serving | replay, interleaving, consistency monitoring |
| LLM | Dirty training data | data engineering | dedup, quality filters, contamination checks |
| LLM | Format conflicts (pre-train vs post-train) | data engineering | neutral separators, chat-template masking |
| LLM | Delayed/poisoned reward | RL data | reward modeling, human-feedback loops, gaming checks |
| Agentic | Tool-result failure recovery | trace construction | noise injection, error-recovery trajectories |
| Agentic | Sparse agentic data | data engineering | notebook/trace mining, synthetic tool-use |
| Multimodal | Modality imbalance | sample construction | per-modality sampling, codebook collapse checks |
| Serving | Latency vs quality | serving | cascade cuts, pre-rank budgets, cache placement |

## The audit queue

Each entry names the section, the stage range, and the status. A section is
`pending`, `in progress`, or `done`; `done` means every stage in it satisfies
the audit contract above.

### Personalized discovery — recommendation 56-63

**Status: done (first audit increment, 2026-08-07).**

Failure modes audited with measured runs: entire-space funnel (CTCVR under
sparse CTR), delayed feedback (freshness vs correctness, window size),
negative sampling (calibration vs ranking, ratio misestimation, extreme
negative rates), exposure bias (IPS vs naive, thin exploration traffic, noisy
propensity), heavy-tail objectives (AOV skew, whale dominance), multi-task
conflict (gradient balancing, gating, dominant-task drift), funnel consistency
(impossible probabilities, constraint cost, order vs click), cascade
consistency (pre-rank vs final ranker, distillation blur, top-k preservation).

### Personalized discovery — shared 00-09 (retrieval to report)

**Status: done (second audit increment, 2026-08-07).**

Every stage 00-09 satisfies the contract: each opens with an operational
symptom (the split that leaks, the latency that kills the page, the rule
interaction that returns nothing), each has a `runs/` record with real
measured numbers, and each carries three detours with their own `core/` +
`runs/`. The A/B experiment chapter that the canvas's "Any ranking / A/B
traffic split" row demanded now exists at `shared/54-online-experiments`: a
validity gate (allocation-ratio SRM check, analysis-unit vs randomization-
unit check, switchback serial-dependence check) with three executed
fixtures, plus three failure-mode detours — SRM detection (fires at 2,000
users vs 78,000 for outcome power; Fabijan et al. 2019), unit mismatch and
carryover (24% false positives at declared alpha 5%; washout recovery), and
switchback (53% per-minute false positives; 0.43 block-SD MDE at 80% power;
Bojinov et al. 2023). Cited and dated: Kohavi/Tang/Xu 2020, Fabijan et al.
2019, Tang et al. 2010, Bojinov et al. 2023; the interleaving alternative
links to the ads track's `38-interleaving-experiments`.

### Personalized discovery — shared 43-55 (operations)

**Status: done (third audit increment, 2026-08-07).**

Stages 43-47 now satisfy the contract, each with an executed case-finding
audit, a who-owns-the-loop section, dated citations, and three detours:

- 43 feature store: as-of consistency audit over emitted store reads
  (served-vs-trained delta per key, DIVERGENT verdict); ownership split
  across feature/serving/training-platform; Zipline (Strata 2018) and
  Sculley et al. 2015; detours: divergence, missing default, and the
  refresh cadence (online-value-moves).
- 44 training-serving consistency: logged-versus-live distribution audit
  (per-feature mean/max \|delta\|, DIVERGENT verdict, the comparison
  TFDV encodes); ownership split across logging/serving/label teams;
  TFX (KDD 2017), Breck et al. SysML 2019, Chapelle 2014; detours:
  late label, lagging feature, and the join that looks ahead
  (label-time snapshot leaking the outcome).
- 45 feedback loops: exposure-concentration audit (per-band impression
  share and measured-vs-true CTR, CONCENTRATED verdict); ownership split
  across traffic/logging/ranker teams; Mansoury et al. CIKM 2020,
  Chaney et al. RecSys 2018, Abdollahpouri AIES 2019; detours:
  popularity collapse, filter bubble, and the policy that borrows luck
  (naive vs IPS vs stale-propensity estimates).
- 46 retraining/staleness: per-cohort staleness panel (rank error vs
  snapshot age per cohort, VOLATILE FIRST verdict); ownership split
  across retraining platform/cost owner/monitoring; Verachtert et al.
  2023; detours: metric flip, embedding expiry, and the peak that hits
  (calendar vs error-triggered retrain through a demand spike).
- 47 monitoring/drift: slice-aware drift panel (per-slice EWMA gap,
  HIDDEN SLICE verdict — the "big slice flat, small slice collapsed"
  case); ownership split across monitoring/rollback-authority/feature
  owner; Gama et al. 2014, Breck et al. 2019; detours: noisy alert,
  silent drift, and the slice that hides (small-segment noise: detection
  latency vs false alarms).

Stages 48-55 satisfy the same contract, each with an executed
case-finding audit, a who-owns-the-loop section, dated citations, and
three detours:

- 48 realtime user state: depth-stratified session-lift audit (served
  CTR by session depth and traffic share, SHALLOW SESSION verdict — the
  70%-traffic shallow session earns half the deep-session lift);
  ownership split across serving/session-infra/measurement; Hidasi et
  al. ICLR 2016; detours: realtime-too-expensive, session-state-moves,
  and the session leak (feature window including the label window:
  perfect offline top-1, 33/300 as-of).
- 49 throughput and capacity: load-scan deadline audit (p95 vs the
  100ms deadline per load, DEADLINE UNACHIEVABLE verdict — mean capacity
  is the divergence load, not the serving answer); ownership split
  across serving/capacity-planning/measurement; Dean & Barroso CACM
  2013; detours: peak-arrives, tail-costs, and the fanout that
  multiplies the tail (1.1% over-500ms single shard to 18.5% at fanout
  20; hedging).
- 50 cost per query: attribution audit across catalogue scale (recall
  candidates grow sublinearly, RECALL DOMINANT verdict — recall owns
  68% of cost at 1B items); ownership split across recall/fine-rank/
  cost owner; Han, Mao & Dally ICLR 2016; detours: cache-pays,
  model-too-big, and the tail that misses the cache (head discount, not
  a capacity plan).
- 51 new-user experience: onboarding-path cohort audit (first-page NDCG
  and retention per path vs the no-ask baseline, NEW-USER GAP verdict —
  a confident wrong prior is worse than asking nothing); ownership
  split across growth/cold-start-ranking/measurement; Abdullah et al.
  Applied Sciences 2021; detours: personalization-scares, user-is-new,
  and the bandit that explores (greedy 0.817 runway avg vs 0.728 at 30%
  epsilon; exploration is a tax on a short runway; Thompson 1933).
- 52 trust and explainability: explanation-surface audit (headline
  verifiability per surface vs the aggregate, UNVERIFIABLE HEADLINE
  verdict — the similar-users surface leads with an uncheckable claim
  on 70% of items); ownership split across ranking/product/measurement;
  Zhang & Chen FTIR 2020; detours: explanation-is-wrong, trust-erodes,
  and the attribution that shifts with the baseline (headline flips
  unverifiable-to-verifiable; Lundberg & Lee NeurIPS 2017).
- 53 fairness and allocation: floor-level allocation audit (declared
  floor vs the protected group's served exposure, GROUP GAP verdict —
  renormalisation re-dilutes the floored group); ownership split across
  ranking/policy/measurement; Abdollahpouri et al. KDD workshop 2020;
  detours: constraint-bites, policy-is-biased, and the groups that
  cross (the fairness verdict flips with the definition; Ekstrand et
  al. FAT* 2018).
- 54 online experiments: validity gate with three executed fixtures
  (SRM chi2 21.52 p=3.5e-06, unit-mismatch SE gap 3.19x, switchback
  serial dependence); ownership split across
  experimentation-platform/analysis/product; Kohavi/Tang/Xu 2020,
  Fabijan et al. 2019, Tang et al. 2010, Bojinov et al. 2023; detours:
  split-lies, user-crosses-groups, traffic-is-two-sided.
- 55 LTV and CAC: per-window unit-economics audit (LTV/CAC per measured
  horizon, WINDOW TRUNCATED verdict — the window decides which channel
  is the acquisition bet); ownership split across
  growth-finance/acquisition/analytics; Fader, Hardie & Lee Marketing
  Science 2005, Gupta et al. JMR 2004; detours: cac-exceeds-ltv,
  retention-flattens, and the retention window that truncates (3-month
  view ranks paid above referral; 24-month reverses it 11.78 vs 0.97).

### Personalized discovery — search 10-24, 35-37

**Status: in progress (search mainline 10-13 audited, 2026-08-07).**

Stages 10-13 now satisfy the contract, each with an executed case-finding
audit, a who-owns-the-loop section, dated citations, and three detours:

- 10 query understanding: intent-mix audit over a 32-query log
  (head/tail stratification; all three keyword collisions are tail
  queries, 15% of tail vs 0% of head — INTENT COLLISION verdict);
  ownership split across query-understanding/retrieval/data teams;
  Kumar et al. 2020 (click-derived intent labels); detours: misspelled
  query, short query, and the intent that misroutes (four of seven
  queries keep NDCG@3 at 1.0000 while collision and no-signal queries
  collapse to 0.3333 — the candidate set is the wrong type before
  ranking runs).
- 11 search retrieval: lexical recall audit over declared relevance
  (recall@3 per query vs term overlap; the tail query loses a relevant
  doc scoring 0.0000 — LEXICAL GAP verdict, aggregate recall 0.90 hides
  it); ownership split across retrieval/query-understanding/relevance
  teams; Robertson & Zaragoza 2009, Karpukhin et al. 2020; detours:
  synonym under-rank, dense path, and the vocabulary mismatch that cuts
  the candidate (unexpanded recall@3 0.00; expansion recovers to 1.00
  at the cost of a false positive).
- 12 search ranking: pairwise label-consistency audit over three grading
  batches (direction disagreements plus learned-preference flips;
  NDCG@A swings 0.5727-0.6209 with zero model change — PAIRWISE
  INCONSISTENT verdict, and a direction-only gate undercounts);
  ownership split across labeling/ranking/evaluation teams; Burges 2010;
  detours: click label, longer list, and the label that is relative
  (12 of 13 single grade flips leave the ranker unchanged; the visible
  flip sits on the smallest-margin learned boundary).
- 13 search evaluation: metric-divergence audit over seven graded
  rankings (competition-style leaderboards; MRR ties five rankings as
  joint best that NDCG separates across five ranks — METRIC DIVERGENCE
  verdict, rank gaps 2-4); ownership split across
  evaluation/ranking/product teams; Järvelin & Kekäläinen 2002,
  Joachims 2002; detours: mrr-vs-ndcg, the k that changes the claim,
  and the metric that is gamed (the mrr gamer ties the honest spread at
  MRR 1.0000 while NDCG falls to 0.7519; the ndcg gamer normalizes to
  1.0000 with an empty tail).

Remaining in this section (pending): expansion 19, dense retrieval 20,
hybrid fusion 21, reranking 22, personalized search 23, measurement 24,
generative retrieval 35, conversational search 36, LLM query
understanding 37. Each needs the same audit contract, with the head/tail
coverage and offline-consistency detail stages 10-13 now set.

### Personalized discovery — ads 14-18, 25-30, 38-42, 54

**Status: pending.**

Audit auction, eCPM ranking, calibration, pacing, externality, frequency
capping, creative selection, bid strategy, auction revenue, RTB pipeline, ads
measurement, interleaving, first-price transition, privacy-safe attribution,
LLM creative generation, marketplace economics, advertiser ROAS. Ads is where
the A/B and traffic-split detail belongs most.

### Personalized discovery — recommendation 31-34 (frontier)

**Status: pending.**

Audit LLM ranking, recommendation RLHF, multimodal recall, slate evaluation.
Add the offline-consistency and reward-gaming depth that the 56-63 audit
established as the standard.

### Language-model system — 00-07

**Status: pending.**

Audit the LLM track with the same lens: dirty data and washing (dedup,
quality filters, contamination), tokenizer edge cases, pretraining data mix
(sample, RL, SFT, agentic data and how each enters pretraining), format
conflicts between pre-train and post-train, distillation failure modes, RL
reward gaming, eval gates, and serving/cascade latency. The model-processing
and sample-construction detail the user asks for lives here.

### Foundations, infra-absorbed chapters, and remaining missions

**Status: pending.**

Audit foundations for the failure-mode lens (optimization plateaus, dead
experts, significance under multiple testing), the multimodal generation
track (codebook collapse, modality imbalance, streaming decode), quantitative
research (as-of joins, restatements, purge), agentic platform (tool-result
recovery), game AI (policy collapse, closed-loop divergence), bio-pharma
modeling, and autonomous driving (perception failure, distribution shift,
closed-loop evaluation).

## How an audit is marked done

An audit is done when every stage in the section:

- has a chapter whose opening question is an operational symptom, not a
  mechanism;
- has a `runs/` record with real measured numbers for the fix and its cost;
- names the pipeline stage that owns the failure mode and the cross-team
  handoff;
- cites the research and industry practice it relies on, dated;
- is reachable from the sidebar and named by at least one topic in
  `site/topics.mdx`.

The queue is worked in order, one section at a time, and a section is never
half-audited: it stays `in progress` until the whole stage range passes.
