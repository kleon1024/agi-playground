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
| Recommendation | AUC-label seesaw | model structure, evaluation | stratified AUC, calibration guardrails, multi-task gating |
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

**Status: done (search mainline 10-13, advanced 19-24, and frontier
35-37, 2026-08-07).**

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

Stages 19-24 now satisfy the same contract, each with an executed
case-finding audit, a who-owns-the-loop section, dated citations, and
three detours:

- 19 query expansion: expansion-lift audit over a 24-query log
  (head/tail stratification; head queries recover 0.000 and take on
  1.00 noise each while the tail carries all +0.467 of the lift —
  EXPANSION LIFT CONCENTRATED IN THE TAIL verdict); ownership split
  across expansion/retrieval/data teams; Xu & Croft 1996; detours:
  expansion hurts, correction helps, and the typo that is a real word
  (a valid catalog term never fires edit-distance correction — the
  evidence has to come from the click log; Hirst & Budanitsky 2005).
- 20 dense retrieval: stale-embedding audit over a 20-query log
  (fresh-versus-stale recall@5; tail queries lose 0.600 against 0.060
  on head — STALE EMBEDDING DIVERGES IN THE TAIL verdict); ownership
  split across model/serving/evaluation teams; Huang et al. KDD 2020;
  detours: stale embedding, ANN index, and the space where everything
  is equidistant (anisotropy packs five cosines into +0.975..+0.990
  and inverts the ranking; Ethayarajh et al. ACL 2019, Gao et al.
  ICLR 2019).
- 21 hybrid fusion: fusion-weight audit over a 20-query log (NDCG at
  three weights; tail swings 0.343 against 0.020 on head — WEIGHT SWING
  CONCENTRATED IN THE TAIL verdict); ownership split across
  fusion/retrieval/evaluation teams; Cormack, Clarke & Büttcher SIGIR
  2009; detours: empty set, weight moves, and the sets that disagree
  entirely (disjoint lists give RRF nothing to reward and the page top
  is a coin flip; the check is the served overlap rate).
- 22 reranking: served-k audit over a 20-query log (NDCG@10 versus
  NDCG@3; tail improves +0.080 at @10 while collapsing -0.080 at the
  served @3 — SERVING-K DIVERGENCE verdict); ownership split across
  ranking/serving/evaluation teams; Nogueira & Cho 2019; detours:
  tight budget, reranker disagreement, and the gain below the fold
  (NDCG@10 0.9592 to 0.9758 while the three-slot page worsens 1.0000
  to 0.9677 — the eval k and the served k disagree).
- 23 personalized search: personalization-lift audit over a 16-query
  log crossing history depth with query stratum (heavy-history tail
  lifts +0.250; new users get 0.000 to -0.020 — LIFT CONCENTRATED IN
  HEAVY-HISTORY USERS verdict); ownership split across
  personalization/ranking/data teams; Dou, Song & Wen WWW 2007;
  detours: personalization hurts, history helps, and the new user who
  is the majority (70% no-history traffic dilutes a +0.150 slice lift
  to +0.019 aggregate — the product decision is the cold-start
  policy).
- 24 search measurement: funnel audit over four slices (device crossed
  with query stratum; mobile-tail converts at 0.20% against a 1.67%
  aggregate with a 25% zero-result rate — HIDDEN SLICE verdict);
  ownership split across analytics/product/data teams; Jones &
  Klinkner CIKM 2008; detours: click-is-a-query, zero-rate matters,
  and the session definition that moves (the same log reports 100%
  success under a timeout and 40% under topic continuation — the
  definition has to be frozen before the numbers mean anything).

Stages 35-37 now satisfy the same contract, each with an executed
case-finding audit, a who-owns-the-loop section, dated citations, and
three detours:

- 35 generative retrieval: decode-recall audit over a 20-query log
  (head/tail stratification; head decodes at 1.000 recall and 1.000
  precision while tail recall is 0.540 with 0.740 emitted-ID precision
  — DECODE RECALL DIVERGES IN THE TAIL verdict, aggregate recall 0.770
  is a head artifact); ownership split across
  generative-model/serving-fallback/evaluation teams; Tay et al.
  NeurIPS 2022 (DSI); detours: id-space-grows, generator-hallucinates,
  and the ID that is a phrase (substring IDs name 5 of 8 titles, so
  the no-index claim softens once IDs are human-readable; Bevilacqua
  et al. NeurIPS 2022).
- 36 conversational search: resolution-stability audit over a
  10-session log (session-length stratification; 2-4 turn sessions
  resolve at 0.980, 12-24 turn sessions at 0.380 — RESOLUTION LOST IN
  LONG SESSIONS verdict, aggregate 0.680 is a short-session artifact);
  ownership split across conversational-search/query-understanding/
  product teams; Radlinski & Craswell CHIIR 2017, Liu et al. TACL
  2024 (Lost in the Middle); detours: topic-shift, anaphora-ambiguous,
  and the context that is long (truncation drops the first-turn
  grounding first; resolution of "back to the first pair" falls from
  1.0 at 8 turns to 0.1 at 24).
- 37 LLM query understanding: parse-stability audit over a 10-query log
  with five sampled parses per query (head parses agree at 1.000 and
  score 0.976; tail agrees at 0.520 with 2.4 low-confidence slots per
  query — PARSE QUALITY HIDES SWINGING JUDGMENT CALLS verdict,
  aggregate 0.765 is a head artifact); ownership split across
  query-understanding/retrieval/product teams; Wang et al. ICLR 2023
  (self-consistency); detours: over-parses, empty-slot, and the parse
  that swings ("apple watch" splits 3-2 product/service across
  samples, so a thin majority broadens or clarifies instead of
  committing).

### Personalized discovery — ads 14-18, 25-30, 38-42, 54

**Status: done for 14-18, 25-30, and 38-42/54 (fourth, seventh, and
eighth audit increments, 2026-08-07/08).**

Stages 14-18 now satisfy the contract, each with an executed case-finding
audit, a who-owns-the-loop section, dated citations, and three detours:

- 14 ad auction: competition-stratified revenue audit over 20,000
  auctions per bidder count (rev/auction 0.2514 with one bidder vs
  0.6118 with four vs 0.7776 with eight; reserve-bound share 100% to
  3.1% — THIN MARKET verdict, fill stays alive while revenue
  collapses); ownership split across marketplace/demand-acquisition/
  measurement teams; Vickrey 1961, Myerson 1981, Edelman/Ostrovsky/
  Schwarz 2007, Varian 2007; detours: reserve-price-bites,
  truthful-bidding, and when-the-market-is-thin (one-bidder reserve
  sweep humps at 0.2492 near reserve 0.50 — depth beats reserve
  tuning).
- 15 eCPM ranking: rank-error audit over an 18-cell perturbation grid
  (7 winner flips, 38.9%; mean realized 136.11 vs optimal 150.00, loss
  13.89 per impression — ESTIMATE FLIP verdict, half-measure errors
  cost nothing while flips cost 30-50); ownership split across
  ranking/calibration, pricing/auction, measurement teams; Guo et al.
  2017, Naeini et al. 2015, Varian 2007, Cavallo & Wilkens 2014;
  detours: pctr-moves-the-rank, reserve-interacts, and
  when-the-bids-tie (tie-break rule realizes 100.00 vs 120.00/80.00
  under true pCTR — the rule, not the estimate, decides).
- 16 pCTR calibration: slice-stratified ECE audit over 20,000
  impressions (aggregate 0.0238 passes; mobile slice 0.2303 against
  desktop 0.0042 — HIDDEN SLICE verdict, a 90% calibrated majority
  dilutes a 10% broken slice); ownership split across model/data-
  logging/measurement teams; Guo et al. 2017, Naeini et al. 2015,
  Platt 1999, Zadrozny & Elkan 2002; detours: correction-needed,
  calibration-ranking-conflict, and when-calibration-drifts (a stale
  factor that fixes ECE 0.2450 to 0.0000 over-corrects new traffic to
  0.3000 — the fix has an expiration date).
- 17 budget pacing: cap-tightness sweep over a front-loaded day with an
  evening burst (multiplier 0.50 under-delivers 50.0/100; multiplier
  1.50 spends 100.0 but late-window delivery collapses to 0.0 with 3
  dark hours — SPENDS-BUT-MISSES verdict, total spend hides dark
  hours); ownership split across delivery/campaign-management/
  measurement teams; Agarwal et al. 2014, Xu et al. 2015, Zhang/Yuan/
  Wang 2014, Wang/Zhang/Yuan 2017; detours: delivery-varies,
  budget-is-tiny, and when-the-pacer-overcorrects (gain 3.0 darkens 6
  of 12 hours vs 0 at gain 0.5 — feedback gain, not pacing, is the
  failure).
- 18 ad externality: slice-stratified net-value audit over 20,000 users
  (aggregate +0.0688 passes; engaged slice -0.3249 against casual
  +0.2000 — HIDDEN SLICE verdict, the slice that pays is the one the
  platform can least afford to damage); ownership split across
  value-tree/experimentation/ads-product teams; Blake/Nosko/Tadelis
  2015, Anderson & Coate 2005; detours: slot-is-scarce, ad-is-
  relevant, and when-the-slot-hides-the-whale (average displacement
  0.2307 vs P90/P99 0.9500 — the mean hides the one-in-ten context
  where the ad kills the user's most valuable result).

Stages 25-30 now satisfy the same contract (seventh audit increment,
2026-08-08):

- 25 frequency capping: segment-stratified decay audit over 20,000
  impressions (aggregate mean CTR 0.0328 passes; power slice 0.0133
  with 40.6% dead share — HIDDEN SLICE verdict, the aggregate curve
  keeps serving the segment that stopped clicking); ownership split
  across delivery/frequency-control, segment/model, measurement teams;
  Aharon et al. 2023 (arXiv:2312.05052, soft cap +7.3% revenue),
  Buchbinder et al. 2014 J. Scheduling; detours: when-the-cap-bites,
  when-fatigue-hits, and when-the-counter-drifts (a drifted counter
  serves 36,167 impressions at 0.0355 against a correct 30,000 at
  0.0400, +85.6 clicks on dead impressions — the cap is only as good
  as the counter it reads).
- 26 creative selection: wear-and-exploration audit over 20,000
  placements (greedy lifetime crowns the decaying winner at 635 clicks
  @0.0318; EWMA 828 clicks, +4.1% impressions; Thompson decaying 807
  — STALE-WINNER verdict, the creative that won on history keeps
  winning after it stopped earning its slot); ownership split across
  creative/ranking, model/exploration, measurement teams; Moriwaki
  2019 (arXiv:1908.08936), He et al. 2014 ADKDD; detours:
  when-the-creative-is-stale, when-the-creative-context-changes, and
  when-the-creative-has-no-history (epsilon 0.00/0.05/0.10/0.20 serves
  the new creative 0/475/1019/1994 of 20,000 — exploration is the only
  way a cold creative earns its prior).
- 27 bid strategy: winner's-log audit over 100,000 auctions (true CVR
  0.0188 at \$0.09 eCPM; naive winner's-log estimate 0.0316 at \$0.16,
  overbid 1.68x; IPW restores 0.0187 at \$0.09 — WINNER'S LOG LIES
  verdict, the logged set is the auction's winning half, not its
  population); ownership split across bidder/auction-interface,
  model/calibration, measurement teams; Chapelle 2014 KDD (delayed
  feedback); detours: when-the-target-cpa-binds, when-the-bid-is-
  capped, and when-the-conversion-lags (a 7-day snapshot under-reads
  true CVR 0.0200 as 0.0096, 52% off — the bid optimizes the label
  the log has, not the one that settles).
- 28 auction revenue: shading-dynamics audit over 12 rounds x 300
  auctions with three learning bidders (naive first-price round 1
  revenue 0.7485; converges to 0.4980 by rounds 10-12, within 0.4% of
  second-price 0.5000 — REVENUE LEARNS ITS WAY DOWN verdict, the
  first-price advantage erodes as bidders shade); ownership split
  across auction/pricing, demand/bidder, measurement teams; Google
  first-price transition (2019-09-04), Vickrey 1961, Edelman/
  Ostrovsky/Schwarz 2007, Varian 2007, Myerson 1981; detours:
  when-first-price-pays-more, when-the-reserve-moves-revenue, and
  when-the-bidders-learn (a day-one read of 0.7485 overstates the
  settled 0.4772 by 57% — first-price revenue must be measured after
  the market learns).
- 29 RTB pipeline: tail-latency audit over 20,000 requests across six
  lognormal stages (p50 81.7ms and p95 99.5ms fit the 100ms deadline;
  p99 108.2ms blows it and 933 requests, 4.7%, time out — P99 LOSES
  THE AUCTION verdict, the mean hides the tail that never bids);
  ownership split across RTB-engineering/exchange-facing, model/
  serving, feature/data teams; Yuan/Wang/Zhao 2013 (arXiv:1306.6542),
  OpenRTB 2.5 `tmax`; detours: when-the-bidder-is-slow,
  when-the-exchange-times-out, and when-the-model-outruns-the-budget
  (a heavy model's p99 140.3ms times out 18.0%; a cascade fallback
  cuts that to 6.9% at the price of cheap bids on 33.1% of requests —
  the deadline is a tail constraint and the margin is the budget).
- 30 ads measurement: lift-power audit around the stage's own 0.4-point
  increment (0.032 vs 0.028, binomial noise, fixed seed; at 8,000
  users per arm the observed lift is 0.0000 with the CI covering zero;
  the CI first excludes zero at 20,000, p = 0.040 — SMALL LIFT
  INVISIBLE verdict, the increment that paid for the campaign is
  invisible to the experiment that measured it); ownership split
  across experimentation/measurement, ads-platform/holdout,
  advertiser/budget teams; Lewis & Rao 2015 QJE, Blake/Nosko/Tadelis
  2015 Econometrica, Kohavi/Tang/Xu 2020; detours:
  when-attribution-overcounts, when-the-incrementality-is-zero, and
  when-the-lift-is-too-small-to-see (CI half-width 0.47 points at
  10,000 users per arm against a 0.4-point increment; 80% power needs
  28,547 users per arm — the experiment is sized for the effect).

Stages 38-42 and 54 now satisfy the same contract (eighth audit
increment, 2026-08-08):

- 38 interleaving: position-credit asymmetry audit over 10,000 sessions
  on the stage's own position-click model (naive blend credits A 59.2%/
  B 40.8% against equal teams; balanced random start restores 49.7%/
  50.3% — THE BLEND DECIDES THE WINNER verdict, the winner changes
  with the credit rule); ownership split across experimentation/
  ranking/delivery teams; Joachims et al. 2005 SIGIR, Radlinski &
  Craswell 2010 SIGIR, Schuth/Hofmann/Radlinski 2015 SIGIR, Zhang et
  al. 2025 arXiv:2508.00751; detours: blend-biases-the-credit (naive
  credits A 59.3% and at 200,000 sessions misses the true 50/50 by 78
  standard errors; the random-start fix costs 3.6% more sessions),
  traffic-is-tiny (800 users never reach significance where
  interleaving ships at 400), credit-is-unbalanced (a document in both
  rankings credits both teams without a tie rule).
- 39 first-price transition: shading-error audit holding the bidder's
  belief fixed (U[0,1] belief vs stronger U[0.3,1.3] truth loses 0.022
  per auction; vs weaker U[0,0.4] loses 0.100 of the 0.250 optimum —
  THE ESTIMATE DECIDES THE NET verdict, belief error squared over four
  lands directly in net); ownership split across bidder/auction/
  forecast teams; Vickrey 1961, Edelman/Ostrovsky/Schwarz 2007, Varian
  2007, Google first-price transition (2019-09-04); detours:
  competition-is-unobservable (100 trials per probe moves the fitted
  optimum to 0.60 and loses 0.011 per auction — the second-price log
  that revealed competitor bids is gone), shading-is-wrong,
  market-adjusts (platform revenue falls from \$0.95 to \$0.42 per
  auction as bidders learn to shade).
- 40 privacy-safe attribution: epsilon-flip audit over 1,000 draws per
  level (at the stage's epsilon 2.0 the close pair flips 12.9% and
  twelve weekly reports flip at least once with 81% probability; at
  0.5 the top-1 flips 16.7% — THE NOISE FLIPS THE ORDER THAT SPENDS
  THE BUDGET verdict, epsilon must clear the gap that matters);
  ownership split across privacy-dial/report-shape/budget-split teams;
  Dwork 2006 ICALP, PoPETs 2024 arXiv:2403.15224, arXiv:2406.02463,
  Apple AdAttributionKit (WWDC24); detours: noise-flips-the-order (six
  channels flip 87.6% vs 12.3% for three at epsilon 2.0 — report shape
  is a privacy cost), noise-is-too-high, budget-splits (100 reports
  dilute epsilon 2.0 to 0.02 each with noise scale 50).
- 41 LLM creative generation: surface-score audit over 5,000 batches of
  10 variants (surface selection misses the CTR-best on 55.1% of
  batches with 7.3% mean relative CTR loss, chosen 0.0848 vs best
  0.0914 — THE SURFACE SCORE PICKS THE CREATIVE THAT DOES NOT CONVERT
  verdict); ownership split across generation/selection/delivery
  teams; Keon et al. 2025 arXiv:2509.25767, Mita et al. 2024 ACL
  long.54; detours: generator-collapses-to-the-train-set (collapse 0.6
  cuts delivered CTR from 0.0911 to 0.0515 with 59.8% re-runs and a
  0.0406 within-flight decay), score-is-on-surface,
  generated-creative-is-identical (three variants normalize to two
  messages, so selection is choosing between a copy and a punctuation
  edit).
- 42 marketplace economics: elasticity sweep over three demand slopes
  (peak 42.0% on the sticky curve, 31.0% on the stage's curve, 25.0%
  on the elastic one; the fixed 35% earns \$203 vs \$105 across the
  outer curves, 48% apart — THE DEMAND CURVE SETS THE PEAK verdict, a
  rate fitted to one curve is a bet on one market); ownership split
  across pricing/two-sided-growth/finance-ads-operations teams; Rysman
  2009 JEP, Rochet & Tirole 2003 JEEA, Weyl 2010 AER, Evans 2009 JEP;
  detours: demand-curve-is-elastic (two-sided peak 21.0% vs one-sided
  31.0%, and pricing at the one-sided optimum earns 15% below the
  two-sided peak), take-rate-is-too-high, ad-load-moves.
- 54 advertiser ROAS: marginal-versus-average audit over \$500
  increments (average ROAS stays above 5.0 from \$1,000 to \$3,000
  while marginal ROAS falls to 1.96; cutting from the top loses \$980
  per \$500 where the first increment loses \$2,604 — THE AVERAGE HIDES
  THE MARGIN verdict, the budget decided on average ROAS keeps
  spending where the next dollar already loses); ownership split
  across media-buyer/measurement/finance-reporting teams; Blake/Nosko/
  Tadelis 2015 Econometrica, Lewis & Rao 2015 QJE, Google Ads
  marginal-ROAS support doc (consulted 2026-08-08); detours:
  average-hides-the-margin (the marginal dollar returns 1.96x while
  the average says 5.21x), roas-collapses, budget-moves.

### Personalized discovery — recommendation 31-34 (frontier)

**Status: done (fifth audit increment, 2026-08-07).**

Stages 31-34 now satisfy the contract, each with an executed case-finding
audit, a who-owns-the-loop section, dated citations, and three detours:

- 31 LLM ranking: prompt-order audit over a 20-query log (head/tail
  stratification; head swings 0/10 with displacement 0.000 while tail
  swings 10/10 with displacement 1.040 — PROMPT ORDER SWINGS THE
  REORDER IN THE TAIL verdict); ownership split across ranking/serving/
  evaluation teams; Sun et al. 2023 (arXiv:2304.09542), Qin et al. 2023
  (arXiv:2306.17563); detours: llm-disagrees, prompt-token-budget, and
  the output that cannot be parsed (5/12 responses invalid, naive parse
  serves 5 dropped docs plus a phantom; validate-and-resample repairs
  5/5 at the cost of 5 extra inference calls).
- 32 recommendation RLHF: pair-margin audit over a 20-pair log (head
  mean margin 1.140 with 0/10 flips, tail mean margin 0.039 with 4/10
  flips — NEAR-TIE PREFERENCES FLIP UNDER LABEL NOISE verdict);
  ownership split across labeling/ranking/evaluation teams; Rafailov et
  al. NeurIPS 2023, Zhang et al. ICML 2025 (arXiv:2410.02197); detours:
  preference-is-noisy, reward-is-gamed, and the preference cycle the
  scalar model cannot hold (A>B> C>A: Elo fit predicts 2/3 edges wrong
  and the last-update swing 0.659 never decays).
- 33 multimodal recall: modality-coverage audit over a 20-item log
  (head both-modality 100%/single 0%, tail single 100% — SINGLE-
  MODALITY ITEMS ARE HALF-REACHABLE verdict, aggregate reachable 100%
  hides it); ownership split across content-embedding/serving/
  evaluation teams; Radford et al. ICML 2021, Liang et al. NeurIPS
  2022; detours: image-is-cold, modality-mismatch, and the content
  vector that is low quality (recall@3 drops from 8/8 clean to 2/4
  low-quality; displaced items lose to other categories' items).
- 34 slate-vs-item evaluation: metric-agreement audit over a
  20-comparison log (head agrees 10/10, tail flips 0/10 — THE METRICS
  AGREE ON HEAD SLATES AND FLIP ON TAIL SLATES verdict); ownership
  split across ranking/evaluation/serving teams; Ie et al. IJCAI 2019,
  Craswell et al. WSDM 2008; detours: slate-is-diverse,
  metric-misses-diversity, and the position that matters (relevance
  best 0.95 item in slot three clicks 0.285 vs the promoted 0.90 item
  at 0.900 — clicks measure the slot, not the item).

The offline-consistency and reward-gaming depth the 56-63 audit
established is now present: stage 32 carries the gamed-reward detour
and stage 34 carries the position-bias case that explains why raw
click feedback cannot stand in for slate value.

### Personalized discovery — recommendation model structure and label health

**Status: done (sixth audit increment, 2026-08-07).**

The two failure modes the reader meets first on the job now have their
own stages (64 and 65), each with an executed case-finding audit, a
who-owns-the-loop section, dated citations, and three detours:

- 64 AUC-label seesaw: main path rewritten answer-first for readability —
  the seesaw (跷跷板, PLE, Tang et al., RecSys 2020) is a structural
  trade, the decision is a pre-declared contract (primary metric +
  guardrail thresholds) that turns "some up, some down" into pass/fail,
  and the local 2,560-row cohort is labeled a mechanism demo per the
  evidence-scale rule, with the decision practice cited to Kohavi & Tang
  (2017) guardrail metrics. Mechanism (one gradient, correlated labels,
  one shared bottle) and the move-the-trade toolkit (weight dial first,
  MMoE/PLE when the dial cannot, gradient surgery last) each get a short
  readable section; the stratified audit, gradient-conflict numbers, and
  the calibration axis live in the three detours, out of the main path.
- 65 sparse labels: a cold-slice run over 8,000 rows (cold-only 0.678,
  shared trunk 0.780, surrogate 0.696) and a density audit whose verdict
  is THE AGGREGATE AUC IS A DENSE-SLICE NUMBER — cold-item 2 positives
  in 260 rows with a 5-95% interval spanning chance ([0.500, 0.957]),
  delay median 0.39d with 11% in flight at the 0.6d snapshot. Ownership
  split across sample-and-label/model/evaluation teams; citations to
  Chapelle et al. KDD 2014, Ktena et al. RecSys 2019, Yasui et al.
  CIKM 2020. Detours: the interval arithmetic (width 1.000 at k=2 to
  0.517 at k=30 — a label-supply fact), the surrogate bleed (fills the
  slice but inflates predicted purchase ~11x and loses true-label AUC
  0.706 vs 0.756), and warm start (misaligned click trunk 0.659 loses to
  scratch 0.740; aligned head-slice buy trunk 0.786 wins).

The depth the 56-63 audit established is now present on the model-structure
side: the stratified metric contract, the calibration axis, and the
label-supply guardrail each name who owns the loop and which guardrail
proves the fix worked.

### Language-model system — 00-07

**Status: in progress (00-corpus data health, 01-tokenizer tie-break,
02-pretrain divergence, 03-sft template contract and distillation,
04-rl delayed/poisoned reward, 05-serve cascade, 06-agent recovery,
07-eval gates audited, 2026-08-07).**

Stage 00 now carries the dirty-data failure the queue named first: a
benchmark-contamination chapter with an executed run over 200 items, 60
leaks at three edit levels, and four detectors — exact hash catches only
verbatim copies, a 13-gram overlap pass (Brown et al. 2020) catches 19/20
near copies with zero background false positives, MinHash near-duplicate
detection (Lee et al. 2022) is a recall dial (13/20 at threshold 0.7,
17/20 at 0.5), and paraphrases evade every detector yet still teach their
20 answers (fact-level recovery 60/200 vs strong-signal 40/200; clean
corpus 0/200) — with ownership split across data/evaluation/release
teams and the before-training gate made explicit. The release-policy
detour's LSH threshold S-curve is now measured, not just computed
(16x4 measured vs formula: 0.680 vs 0.644 at J=0.5, 0.987 vs 0.988 at
J=0.7; 32x4 threshold shift 0.50 to 0.42).

Stage 02's curve-divergence chapter is now executed, not asserted: the
pair-reading table (read the pair, not the line) is backed by a planted
run with four injected failures. Too-high LR spikes both curves with no
recovery and its gradient-norm trace departs from baseline two steps
before the loss does (step 4: 0.600 vs 0.197 at baseline, loss still
2.90; step 6 the loss explodes); softmax overflow in fp32 range goes
non-finite at step 3, where a non-finite check stops and attributes the
step while the unchecked run completes with a wall of inf then NaN; a
corrupted batch (steps 100-139) moves train and held-out together and
both return toward the baseline path; and bf16 master weights flatline
the train curve at 2.418 vs the fp32-master 2.358 floor with a gradient
norm still alive at 0.050 — a precision floor, not a dead loop. The
mission's own 3.0689-to-3.0984 anomaly remains unattributed, and the
runs record states the boundary (toy model, planted LR values, bf16
master-weight simulation rather than the full mixed-precision contract).

Stage 03's format-conflict row is now executed on the real contract: the
chat template is measured on the frozen tokenizer, the real masker, and
the real 9,500-conversation no_robots set. The marker is one reserved id
or it is eight byte tokens (byte-split would add ~301k tokens, +11.1% of
the corpus); five serve-time header drift variants diverge from the
trained `assistant\n` at token 0 (capital, leading space) or token 2
(missing newline, extra space, CRLF); and the mask trains on 68.2% of real
tokens on this curated set, with a 1.7% per-block minimum where context
dominates — so the masker's job is exclusion, not density, and its tests
own role-label integrity. Packing drops 217 long conversations and pads
19.6% of block capacity. Ownership split: stage 01 tokenizer freeze owns
the reserved ids, the serve harness owns byte parity (token-id parity
check as guardrail), the data pipeline owns masker tests. The queued
follow-up is now executed (`when-the-role-is-wrong`, 2026-08-07): a
swapped two-turn role turns 213 user tokens into loss targets against 24
clean targets and suppresses the 23 real answer tokens (the decoded
target span is the user's question verbatim); a case-variant role
silently drops the whole turn (0 targets); an empty last turn renders to
exactly one target, the closing marker; content cannot forge a role
boundary (the frozen vocab byte-splits the marker into 8 tokens, never
the reserved id), but a double-rendered row puts 4 literal marker strings
inside the target span; and a stamped all-assistant pipeline (238
targets) passes the last-turn rule, so the guardrail adds role
alternation. The validator catches all five injected classes, and finds
15 real flags across 9,500 no_robots rows (0.16%, all consecutive
duplicate assistant roles; row 741 reads like a user reply labeled
assistant). Guardrail cost: one string scan per row before rendering; the
mechanical classes are rule-caught, ambiguous intent stays a sample
review.

Stage 04's delayed/poisoned-reward row is now executed
(`when-the-reward-is-wrong`, 2026-08-07): on the real 04-rl GRPO trainer,
the parent's Exercise-1 warm start (250 supervised steps over 24
hand-written examples) lifts the tag fire rate to 79.2% (76/96) against the
base run's 200/200 degenerate groups; advantage distortion under flipped
labels moves the decision more than the score — 5% flips change 10% of
group choices (2/20), 20% change 60% (12/20), every changed choice pushes
the wrong completion, while the poisoned-vs-true rank correlation only
slides 0.478 to 0.403; a 30-step clean-vs-10%-flipped comparison shows both
reward curves rising with the poisoned arm higher (roughly 0.2-0.4 vs
0.1-0.3) while held-out true correctness stays near zero in both arms — the
detection is the training-reward/clean-verifier pair, not the curve; and
delay priced as poison decays label agreement as
`0.5 + 0.5 (1 - 2·drift)^lag`, a coin flip at drift 5% / lag 20 (55.5%),
so the error budget belongs in the label pipeline, not the optimizer.
Ownership: the label pipeline owns label trust and staleness, the eval team
owns the verifier and the disagreement threshold, the model team owns the
reward/verifier pair as a run contract. Citations: Rando and Tramèr, ICLR
2024 (arXiv:2311.14455) and Wan et al., ICML 2023 (arXiv:2305.00944); the
delay family cross-links to recommendation's 57-delayed-feedback.

Stage 01's tokenizer row now carries the hidden-axis failure the queue named
next: a tie-break audit (`when-the-tie-break-matters`, 2026-08-07) trains the
same indexed BPE twice on the same 8,500 no_robots turns under two
deterministic tie-break rules. The tie is the norm — 91.7% of 3,840 merge
steps chose from a tie (mean width 25.7, max 194) — one early choice cascades
(first divergence at step 132, merge-set Jaccard 0.508-0.541 across depths),
and the aggregate metric cannot see it: chars/token is 3.418 vs 3.416 while
41.0% of held-out pieces encode differently (only 250 of 96,383 differ in
token count). The divergence lands on numbers and rare characters — the
pre-tokenizer's `\d{1,3}` digit cap produces per-digit pieces for
1,234,567,890, CJK fragments through the 256-byte base, accents split to two
pieces — and the downstream magnitude is cited to Singh et al. (arXiv:2402.14903,
Feb 2024), who show number tokenization measurably changes arithmetic on
frontier models. Ownership split: tokenizer/training-data team owns the
tie-break as a frozen contract (exact-id export check is the acceptance test),
eval team owns piece-level boundary tests including number and rare-unicode
strings, model team owns the arithmetic consequence. The run is a labeled
mechanism demo at vocab 4096 per the evidence-scale rule; no model was
trained.

Stage 07's eval-gate row is now executed (`eval-gates`, 2026-08-07): the
release gate becomes a computation, not a meeting — a declared rule
(per-category ceiling plus aggregate-delta) is swept over synthetic candidates
with hidden true risk, and the sweep shows why any single threshold trades
false blocks for false passes while a hidden second rule quietly sets the
floor of the first (measured crossover at threshold 0.275). Ownership split:
eval team owns gate definition and the sweep, release team owns enforcement
and escalation, model team owns candidate scores and the audit record.
Citations: Anthropic RSP (Sep 19 2023), OpenAI Preparedness Framework
(Dec 18 2023).

Stage 06's agent row now carries the failure syllabus its harness was built
to feed back (`when-the-tool-errors`, 2026-08-07): a deterministic audit
injects all seven ways the real stage-06 tools can fail and measures recovery
per class — blind retry resolves 0/7 (every re-issue returns the identical
failing observation) while a recovery planner resolves 7/7, in three
families: inspect (missing file, wrong directory, non-allowlisted command),
re-scope (metacharacter refusal, timeout, truncated read), and make-it-safe-
to-redo (the timeout-after-write case where the observation says "timed out"
while marker.txt exists — blind retry would run the side effect again).
Two of the seven failures are returned, not raised (`exit=1` output,
truncated reads arrive as ordinary observations), so detection is part of
recovery. Ownership split: trace construction owns error injection into the
mix, eval team owns a per-failure-class recovery rate rather than task
success, harness team owns the idempotency surface that makes retry safe,
model team owns the data-composition consequence. The parent's measured
0/6 real-agent run is the prerequisite failure (no tool-call shape at all);
the recovery-taxonomy magnitude is cited to PALADIN (arXiv:2509.25238, Sep
2025: failure injection + LoRA over 50,000+ recovery-annotated ToolBench
trajectories lifts LLaMA-8B tool success 17.5% to 78.7%) and Chen et al.,
Self-Debug (ICLR 2024, arXiv:2304.05128); the noise-is-what-teaches-recovery
composition point cross-links to stage 02's mid-training section 7.

Stage 05's serving row now carries the cascade-latency failure the queue
named (`when-the-cascade-loses`, 2026-08-07): an early-exit cascade (cheap
model answers steps it is confident about, expensive model takes the rest;
BranchyNet, Teerapittayanon et al., ICPR 2016) is measured over a threshold
sweep, a cheap-model-quality swap, and a hard expensive-call budget. Three
measured failure modes: confidence is not correctness (tau=0.3 accepts 60%
of steps yet matches the target on only 18%; target CE 1.512 is nearly
cheap-only), the escalation tax (tau=0.7/0.9 escalate 92-99% of steps and
the cascade runs slower than the expensive model alone, 0.89-0.98x; a
40-step cheap model escalates 100/100), and the budget cliff (a 5-expensive-
call budget forces 94/100 steps cheap and collapses match to 13%). The
winning band exists (tau=0.5: 1.45x faster at 58% match) and is a product
decision. Ownership split: model team owns the cheap model's confidence-to-
accuracy calibration per slice, serving team owns the threshold/budget pair
tuned on the p95 request, eval team owns the per-slice match/quality metric,
product owner prices the quality loss. Cross-links to stage 05's
when-the-tail-waits p95 discipline and recommendation's 63-cascade-
consistency.

Stage 03's distillation row now carries the teacher-error arm its control
set aside (`when-the-teacher-is-wrong`, 2026-08-07): sequence-level
distillation from a teacher with a systematic wrong belief (every `e`
replaced by `x` in its training corpus) shows the error is carved into the
teacher's output distribution (x rate 10.4% vs 0.0%, clean CE 2.614 vs
1.520), the student inherits it (x rate 15.7% vs 0.0%; the wrong belief
transfers and amplifies), and a no-signal teacher transfers nothing —
student-from-random lands at clean CE 5.840, worse than the untrained base
4.209. Aggregate CE hides the swap (3.386 vs 3.119); the per-class letter
rates are the check. Ownership split: data team owns a per-class accuracy
audit of the teacher before distilling from it, model team owns the
inheritance check on the teacher's known error classes, eval team owns the
ceiling claim (student cannot exceed the teacher on the teacher's errors),
product owner chooses whose answers the student is allowed to inherit.
Citations: Gudibande et al., ICLR 2024 (arXiv:2305.15717, imitation
transfers style/persona but falls short on factuality and coding) and
Stanton et al., NeurIPS 2021 (arXiv:2106.05945, distillation improves
generalization but not by lifting the student past the teacher).

Stage 00's quality-filter row now carries the gate-tuned-on-the-wrong-slice
failure (`when-the-filter-eats-the-signal`, 2026-08-08): a 20,000-doc
synthetic population (60% templated boilerplate, 40% signal, 40% of it a
code-heavy slice) removed at the same 55% rate under two weight sets —
weights tuned on a junk-heavy, code-poor dev slice ate 1,492 signal docs
(18.3% of the signal population, 46.2% of the code-heavy slice, survivor
code share 16% to 19%) while class-stratified balanced weights ate 12
(0.1%, 0.4%, code share 16% to 36%) — so removal rate is a count, not a
judgment, and the drop audit by class is the case-finding step. Ownership
split: data-pipeline team owns gate thresholds and the dev-slice
stratification, eval team owns the gold holdout and per-gate drop audit,
release owner owns the survivor-shift check in the release record.
Citations: Gopher quality classifier (Rae et al., arXiv:2112.11446, Dec
2021), C4 filters (Raffel et al., arXiv:1910.10683, Oct 2020), RefinedWeb
(Penedo et al., arXiv:2306.01116, Jun 2023), FineWeb ablations (Penedo et
al., arXiv:2406.17557, Jun 2024); cross-links to the contamination
detour, the funnel-shape drop-reason audit, and the release contract. The
funnel-shape, dedup-at-scale, release-contract, and contamination detours
now each carry Who-owns-the-loop and a fix-and-trade section before their
evidence boundary.

The pretraining data-mix row is now executed (`when-the-annealed-slice-moves-the-evals`,
2026-08-08): the mix decision is a two-skill seesaw, measured over an
anneal-window sweep from 0 to 10 percent agentic share. Agentic skill
saturates (`A(s) = 1 - exp(-40s)`) while general skill pays a flat
recency-weighted cost (`G(s) = 1 - 1.6s`): the general slice breaches a
`baseline - 10%` guardrail at s = 0.08 with the agentic eval still at 0.959
of its saturating curve, the marginal trade flips between 8 and 10 percent
(1.12 agentic per point against 1.60 general), and the blended number
rises through the breach (0.892 at 5% to 0.916 at 8%) — an aggregate-only
read rewards the move that breaks the contract, and the slice read is the
case-finding step. The zero-share anchor matches the agent stage's
measured 0/6 run. Ownership split: data team owns mix weights, anneal
schedule, and format; eval team owns the per-slice read and guardrails;
model team owns the pre-declared primary-metric contract — the same
contract pattern as the recommendation AUC-label seesaw (stage 64).
Citations: Agentic CPT (arXiv:2509.13310, 2025), GLM-5 (Kili Technology,
2026), DCLM (arXiv:2406.11794, Jun 2024), FineWeb-Edu (arXiv:2406.17557,
Jun 2024), DoReMi (arXiv:2305.13029, May 2023). The mid-training stage
chapter now carries Who-owns-the-loop and a fix-and-trade section before
its evidence boundary.

The RL reward-gaming row is now executed (`when-the-proxy-gets-gamed`,
2026-08-08): a one-dimensional policy walks under gradient ascent on a
proxy whose peak sits past the true quality peak (the reward model's
verbosity blind spot), and the three-signal read catches the divergence.
The proxy rises monotonically (0.19 to 0.97 — success by itself), held-out
quality peaks at step 30 (theta 1.01) then falls to 0.897 (a ten-point
loss reported as gains by the proxy), proxy gain per KL unit collapses
from 19.87 to 0.66 while true quality per KL goes from +7.72 to -0.82
(the last KL is bought at negative quality), and the distribution check —
spurious-keyword rate 6.4% to 42.6%, mean length 60 to 133 — fires at the
divergence step before the held-out eval turns down, so the policy's own
generation distribution is the case-finding step and the proxy-vs-true
disagreement is the verdict. Ownership split: model team owns the reward
and the divergence contract (pre-declared stop conditions, KL leash),
eval team owns the held-out verifier and the distribution check, annotation
team owns the reward model's blind spots. Citations: Gao, Schulman, and
Hilton (arXiv:2210.10760, 2023, inverted U), Skalse et al.
(arXiv:2211.00694, Nov 2022) and Pan et al. (arXiv:2202.03006, Feb 2022)
for reward hacking, Lambert et al. (arXiv:2403.13787, Mar 2024) for
reward-model error rates; cross-links to the recommendation track's gamed
reward and the KL-beta-zero ablation run. The reward-went-up and
when-the-reward-is-wrong chapters now carry Who-owns-the-loop and
fix-and-trade sections before their evidence boundaries.

Audit the LLM track with the same lens: dirty data and washing (dedup,
quality filters, contamination), tokenizer edge cases, pretraining data mix
(sample, RL, SFT, agentic data and how each enters pretraining), format
conflicts between pre-train and post-train, distillation failure modes, RL
reward gaming, eval gates, and serving/cascade latency. The model-processing
and sample-construction detail the user asks for lives here.

### Foundations, infra-absorbed chapters, and remaining missions

**Status: done for foundations 02-optimization, 06-significance, and
07-moe (ninth audit increment, 2026-08-08); the remaining missions below
are still pending.**

The foundations now carry the failure-mode lens the queue named first:

- 02 optimization: plateau audit over a flat-minimum surface under a
  fixed 1,000-step budget (plain SGD ends 6x above the tolerance while
  momentum and Adam converge; an irreducible term makes all four stall at
  the same number — THE PLATEAU IS THE RATE COLLAPSE, NOT THE FLOOR, and
  the optimizer-change diagnostic separates the two classes); ownership
  split across optimizer/infra/research teams; Dauphin et al. 2014
  (arXiv:1406.2572), Sutskever et al. 2013 (ICML), Kingma & Ba 2015
  (ICLR), Loshchilov & Hutter 2017 (ICLR); detours: the flips that
  separate the optimizers (341 vs 47 vs 4 steep-axis flips) and the new
  when-the-training-plateaus (flat stall vs surface floor, measured).
- 06 significance: multiple-comparisons audit over 12 paired comparisons
  (naive alpha 0.05 fires 0.59 false positives per experiment and 44.2
  percent of experiments carry at least one — MORE COMPARISONS, MORE
  CHANCE HITS; Benjamini-Hochberg q=0.10 cuts that to 0.22 and 16.8
  percent at the measured cost of missing the true effect 25/500 vs
  6/500); ownership split across measurement/statistics/product teams;
  Benjamini & Hochberg 1995 (JRSS-B); detours: when-the-interval-decides
  and the new when-the-comparisons-multiply.
- 07 moe: the dead-expert failure read from the recorded routing sweep
  (top-1 under a 4:1 skew leaves one expert at 0/200 while routing
  entropy stays near maximum — THE DEAD EXPERT IS A ROUTING PROBLEM, and
  the fix is the balancing term: auxiliary loss, capacity factor, or
  quantile bias); ownership split across architecture/serving/evaluation
  teams; Fedus, Zoph & Shazeer 2022 (JMLR 23, arXiv:2101.03961), Dai et
  al. 2024 (arXiv:2401.06066), Liu et al. 2024 (arXiv:2412.19437);
  detour: when-the-expert-goes-dead now carries the fix-and-trade.

Audit the remaining missions with the same lens: multimodal generation
(codebook collapse, modality imbalance, streaming decode), quantitative
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
