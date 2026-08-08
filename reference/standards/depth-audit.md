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

**Status: done (fourth audit increment, 2026-08-07/08).**

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

The tokenizer row also now carries the per-class cost ledger the queue's
aggregate-blindness row demanded (`the-characters-that-cost-the-most`,
2026-08-08): the frozen 16,384-id tokenizer is read class by class — English
0.24 tokens/char, CJK 2.96, emoji 4.00 — so a 4,096-token window holds 17,246
characters of English but 1,382 of CJK, and the mixed-document ledger shows
digit/CJK/emoji runs that are 17% of the characters spending 47% of the token
budget. The aggregate chars/token is true and blind at once; the ledger is
the case-finding step, the fix is a per-class budget contract, and the
multilingual-vocab and arithmetic consequences are cited, dated external
results (Ali et al., arXiv:2310.08754, Oct 2023; Singh and Strouse,
arXiv:2402.14903, Feb 2024). Ownership split: tokenizer/training-data team
owns the ledger and the freeze, eval team owns the per-class boundary suite,
product team owns the per-class budget contract.

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

### Language-model — LLM-track increments (tokenizer, mix, SFT, distillation)

**Status: done for the tokenizer edge-case, data-mix, format-conflict, and
distillation, serving/cascade-latency, eval-gate, and remaining 04-rl
rows (nineteenth audit increment, 2026-08-08). The LLM track is now
covered end to end by the audit contract.**

The final increment closes the rows the queue still named:

- Serving/cascade latency. `05-serve/when-the-cascade-loses` now carries
  the fix-and-trade section its who-owns half lacked: the fix is the
  calibration band (threshold set against a measured confidence-to-accuracy
  curve per slice, budget tuned with it on the tail), the trade is that
  every threshold buys one direction and pays in the other (loosening
  admits the confident-wrong band, 60% accepted / 18% match at tau=0.3;
  tightening escalates 92-99% and the cascade runs slower than the target
  alone, 0.98x/0.91x/0.89x; the winning band at tau=0.5 is 1.45x at 58%
  match and is a product decision), and the budget converts a
  quality-preserving gate into a garbage fallback at the tail (13% match
  under the 5-call budget). The stage README and `why-concurrency-pays`
  carry the same sections from the same increment.
- Eval gates. `07-eval/eval-gates` now carries the fix-and-trade section
  its who-owns half lacked: the fix is the joint sweep executed before a
  candidate exists (the 0.275 flat floor is the evidence that the category
  rule stopped binding and the aggregate rule is doing all the work), the
  trade is that no threshold removes both errors (tightening from 0.50 to
  0.05 moves false blocks 0.000 to 0.423; loosening to 0.65 moves false
  passes 0.000 to 1.000), and which side a team accepts is a policy
  decision written before the gate is tuned.
- 04-rl stage chapters beyond the reward-gaming row. `rollout-concurrency`
  names the fix as the scheduling policy rather than more workers (async
  beats lockstep at every pool size, 1.73x at 2 where lockstep pays 20
  batch boundaries against 1.30x at 8 where it pays 5) and the trade as
  staleness for makespan (Noukhovitch et al. 2024/ICLR 2025, AReaL 2025).
  `the-group-relative-trick` names the fix as the statistic plus its
  guardrails (normalize, skip the degenerate group, one-sided clip) and
  the trade as the zero-sum normalization, the skipped gradient of a
  no-variance group, and the 1.2x pessimism cap. `the-kl-leash` names the
  fix as the always-non-negative k3 estimator (the naive difference's
  -0.693 at new/ref 0.5 becomes +0.307) and the trade as softness and
  asymmetry (cutting mass charged harder than adding it, 0.307 vs 0.193;
  beta owns magnitude, the estimator owns sign). `what-a-real-loop-adds`
  names the fixes as the clipped objective, the verifier-as-published-
  artifact, the sampler as part of the loop, and prompt caching — each
  with its trade, carried on the chapter's dated published citations
  (Schulman et al. 2017; Shao et al. Feb 2024; DAPO Mar 2025; GSPO Jul
  2025; GMPO Jul 2025/ICLR 2026; Anthropic 14 Aug 2024; OpenAI 1 Oct 2024)
  per its no-run survey boundary.

The tokenizer, mix, template, and distillation rows of the LLM queue are now
executed:

- Tokenizer edge cases. `is-it-the-same-tokenizer` and its
  `when-the-tie-break-matters` detour now carry the fix-and-trade and
  ownership sections. The parity contract — identical merge lists under a
  pinned tie-break, plus the 60-document / 60,978-token id-parity export
  gate — is priced against its own coverage boundary: the checks prove
  agreement on the tested corpus and depth (1,744 of 16,128 merges), not on
  every input, and the tie-break detour's fix names the hidden assumption
  the parent check holds fixed. Measured: 91.7% of 3,840 merge steps chose
  from a tie (mean width 25.7 pairs), two rules diverge at merge step 132
  and share only about half their decisions by the end, chars/token
  (3.418 vs 3.416) cannot see the divergence while 41.0% of 96,383
  held-out pieces encode differently, and the number-edge regime (digit
  fragmentation through the pre-tokenizer cap, byte fallback) is a
  tokenizer-time decision with a behavioral cost cited to Singh et al.
  (arXiv:2402.14903, Feb 2024). `the-merges-that-build-the-vocab` now
  names the merge sequence as the reviewable audit trail (merge 256 ' t' at
  1,015,622 through merge 16,000 ' catastrophe' at 88) and the
  vocabulary-size decision as the compression-versus-embedding-memory
  policy. Ownership: tokenizer team owns the pinned contract and the merge
  record, data pipeline owns the export gate, model team owns the
  non-convergence symptom, eval owns piece-level boundary tests.
- Data mix. `what-a-release-needs`'s mixture section now carries dated
  anchors: Llama 3 (arXiv:2407.21783, 2024; ~50% general / 25% math and
  reasoning / 17% code / 8% multilingual, chosen by knowledge
  classification and scaling experiments), Qwen3 (Kili Technology, "Data
  Story: Qwen 3," 2026; 36T tokens in three stages with a
  reasoning-heavy middle stage), and Nemotron-CC (Su et al.,
  arXiv:2412.02595, 2024; ACL 2025; filters drop ~90% of a crawl,
  classifier ensembling plus synthetic rephrasing recover up to 90% of the
  filtered content into a 6.3T corpus with about 4x more unique real tokens
  than DCLM, and an 8B model trained on 15T tokens beats Llama 3.1 8B by
  about 5 MMLU points) — plus the recycling principle (the funnel's
  discarded tail is rephrasable, not only deletable) and the
  pretraining/post-training boundary (SFT and RL data enter post-training;
  the only post-training-flavoured pretraining row is the small annealed
  agentic component, cross-linked to mid-training's GLM-5 anchor).
- Format conflicts. `the-template-is-a-contract` and its
  `when-the-role-is-wrong` detour now carry the fix-and-trade sections. The
  fix is three owned guardrails — reserved marker ids at the tokenizer
  freeze (one id vs eight bytes, +11.1% corpus inflation avoided), a single
  render code path with a token-id parity test (catches all five
  header-drift variants, two at token 0), and masker unit tests — priced
  against their trades: vocab headroom spent, template changes now update
  the render and the test together, mask exclusion matters most where
  target share is low (the 1.7% tail vs the 68.2% mean), and packing's 217
  dropped conversations / 19.6% padding is the accepted cost TRL and
  torchtune answer with block-diagonal masks. The role-wrong fix is the
  row-level validator (role membership, non-empty content, marker strings,
  alternation): one string scan per row, all five injected classes caught,
  15 real flags in 9,500 rows (0.16%), with the explicit limit that
  mechanical classes are rule-caught while ambiguous intent stays a sample
  review.
- Distillation. The four-chapter set now carries the fix-and-trade and
  ownership sections. The parent chapter's fix is the measurement contract
  — fixed prompts, step matching (equal epochs would have handed the model
  teachers 32% and 56% more gradient steps), author-neutral scoring
  (held-out loss ranks by author; every arm wins on its own reference
  set), and
  the teacher-strength control — priced against the doubled generation
  budget and the temperature trade (`banana` at T=4 holds 13.16% vs the
  plausible alternative at T=1, 4.73%). `when-the-teacher-is-wrong` names
  the per-class teacher audit and per-class student inheritance check
  (`x` rate 15.7% vs 0.0% inside CEs 3.386 vs 3.119), the ceiling
  constraint, and the no-signal price (5.840 vs a 4.209 base); cited
  Gudibande et al. (arXiv:2305.15717, ICLR 2024) and Stanton et al.
  (arXiv:2106.05945, NeurIPS 2021). `which-teacher-changes-what` makes the
  margin-vs-spread rule the fix (Fable 2, 8, 13; largest margin 3.3 never
  clears smallest spread 6.0) with the deferral to a downstream
  author-neutral harness as the trade. `what-path-two-requires` prices the
  top-k format (4k bytes/token; 192 GB at top-16 on the 3.0B-token corpus)
  against the storage-vs-live trade and names the tokenizer wall as the
  constraint that makes shared-vocabulary strings weak evidence of
  distillation.

### Foundations, infra-absorbed chapters, and remaining missions

**Status: done for foundations 02-optimization, 06-significance, and
07-moe, and for the voice path's modality-imbalance row (ninth and tenth
audit increments, 2026-08-08). The remaining missions named below —
bio-pharma modeling and autonomous driving — were subsequently audited in
full as their own sections (fifteenth and sixteenth audit increments,
2026-08-08).**

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

### Multimodal generation — voice path (modality-imbalance row)

**Status: done (seventeenth audit increment, 2026-08-08).**

Every stage and detour in the voice path now carries the fix-and-trade and
who-owns-the-loop sections the audit contract requires. The row has two
halves: the sample-construction failure (who is actually in the mix) and
the codebook-collapse checks (is the codebook healthy).

The sample-construction half is measured
(`04-multi-speaker/when-the-mix-is-not-what-you-asked`): the naive
speaker-major builder (`speech_data.build_dataset`) slices
`max_utterances` off a speaker-major list, so a 10-speaker request with a
40-utterance cap serves speaker 2277 only — verdict "10 requested, 1
served" in both splits, and "2 requested, 1 served" replaying stage 03's
exact recorded call, which means stage 03's recorded "1-2 speakers" runs
were 1-speaker measurements. The loud failure misdiagnoses itself ("raise
max_utterances or add a speaker" — the real cause is the slice, not
volume) and the completing failure is silent, which is why counting the
served distribution is the case-finding step. The fix is the balanced
builder's per-speaker utterance bound plus its eval-coverage guard; the
trade is per-speaker budget vs corpus scale, with weighted category-aware
sampling as the scale alternative (ESPnet category-power sampler; Google
production ASR fairness rebalancing toward underperforming speaker
cohorts, arXiv:2207.11345, 2022). Ownership split: the dataset-builder
owner holds the served-distribution contract, eval owns the per-split
coverage guard, and the training team inherits whatever the builder
serves. The queued follow-on — the true two-speaker re-run of stage 03
(`runs/2026-08-08-two-speaker-rerun.md`) — is executed: balanced builder,
three seeds, both speakers (2277, 2035) served in both splits, all three
seeds escape with healthy codebooks (eval MSE 0.01521-0.01746, 54-64/64
codes, entropy 0.788-0.813), inside the same healthy band as stage 03's
single-speaker numbers, so the "1-2 speakers" claim is a measured
two-speaker result, not a corrected label. Corpus: LibriSpeech (Panayotov
et al., ICASSP 2015, DOI 10.1109/ICASSP.2015.7178964).

The codebook-collapse half now carries the sections across every stage and
detour, reusing the mission's measured numbers:

- 00 codec: the recipe is the fix — `lr=1e-3` and 600 steps escape the
  silence local minimum that `lr=3e-4` plateaued on (eval MSE 0.01114 vs
  the 0.32510 silence baseline, 27x; 34/64 codes, entropy 0.733); the
  trade is that the recipe is a property of the data-codec pair (stage 03
  shows real speech needs roughly 3x the steps) and a healthy seed is not
  evidence the codebook is safe (seed 7 ends at 15/64 from identical
  code); ownership split across codec owner (architecture and
  lr/steps), eval owner (baseline pair and usage counter — the number a
  loss-only read reports as success), and mission owner (does_not_prove
  boundary).
- 00 why-codebooks-collapse: measuring the collapse as a trajectory turns
  "collapse" into a legible process (1 code at step 0, 2 at 200, 13 at
  300, peaking at 14 with entropy 0.520 at 400, then losing codes before
  ending at 15/64); the trade is that one seed and one configuration
  cannot certify the codebook — the trajectory view is what makes a single
  healthy run insufficient evidence; ownership split across codec owner
  (usage telemetry contract), eval owner (per-seed protocol), and mission
  owner (the handoff stage 04 records at the frontier).
- 00 when-silence-is-a-local-minimum: recognizing the collapse as a local
  minimum redirects the intervention from the loss to the exit (recon MSE
  0.325 at the plateau, 1-2/64 codes; escape 0.32 to 0.03 over ~150
  steps bought by higher LR and longer training); the trade is a
  two-metric discipline where one seems enough; ownership split across
  codec owner (the exit mechanism), eval owner (the usage counter as the
  load-bearing diagnostic), and mission owner (the both-numbers rule).
- 01 streaming-decode: the identity-check discipline plus the two-scale
  latency measurement — correctness at logit level (30/30 clips, max logit
  gap 1.19e-05 against `TOL=2e-5`), speed at the native 48-token length
  and a 500-step stress (naive tail 6.9x, cached 1.3x); the trade is that
  the benefit is length-conditional — at this mission's clip length the
  cache is statistically indistinguishable from full recompute; ownership
  split across serving owner (zero lines changed in the imported engine
  classes), eval owner (logit protocol and timing harness), and mission
  owner (two-scale reporting contract).
- 01 when-the-cache-pays: the two-half claim — cached must reproduce the
  naive completion token-for-token (3/3 clips) before latency counts as a
  speedup (p50 1.43ms to 9.81ms vs 1.15ms to 1.50ms at 500 steps); the
  trade is that the benefit is conditional by construction — a KV cache
  that changed the answer would be a correctness bug that happens to be
  faster; ownership split across serving owner (identity precondition),
  eval owner (two-scale protocol), and report owner (realtime framing).
- 01 when-the-logits-match: identity is checked at logit level, not token
  level — token equality alone would call a confidence shift "identical"
  (max logit gap 1.19e-05, mean 5.27e-06); the trade is that the check is
  stronger than a token-id comparison and therefore load-bearing; a
  nonzero gap would mean the speedup is a different model, not an
  optimization; ownership split across eval owner (the repo's own
  tolerance), serving owner (behavior-preservation contract), and report
  owner (the load-bearing line).
- 02 report: the five-line acceptance contract — codec 0.0111 and LM
  0.2581 each beat both baselines (silence 0.3251 / mean-signal 0.3001),
  the oracle lands at 0.0113, the offline-vs-streaming gap is a true zero
  (1.19e-05), and zero lines of reused code changed; the trade is that MET
  says nothing about difficulty and a single collapsed verdict would hide
  which line was load-bearing; ownership split across report owner
  (reading-only verdict contract), stage owners (JSON artifacts), and
  mission owner (the five lines declared in `mission.yaml` before stage 00
  existed).
- 03 real speech and network: the controlled step sweep at the unchanged
  LR — 600 steps collapse on real speech (0.0272 ties silence, 1/64),
  2000 steps escape by ~step 1400-1800 (0.01306-0.01369, 51-63/64,
  entropy 0.787-0.870) while `lr=3e-3` never escapes (0.02722, 3/64) — so
  the fix is more time in the recipe, not a higher rate, and the network
  tail (p50 9.66ms, p95 42.46ms, max 85.25ms) is real but path-specific;
  the trade is the input-dependent escape window and the data-label
  correction, now settled by the balanced two-speaker re-run (above);
  ownership split across data owner (served-mix label and balanced
  builder), recipe owner (step-count fix and the sweep that proved it),
  and network owner (this link's numbers, never merged with local decode
  latency).
- 04 multi-speaker: the balanced per-speaker builder plus the three-seed
  protocol — 10 speakers actually served, no seed fully collapsing
  (18/63/32 of 64 codes, margins 4.3%-38.2%, KV-cache check still holds
  at 2.22e-05); the trade is that scaling the claim turns the reliable
  escape into seed-dependence — the frontier stage 05's reset exists to
  close; ownership split across dataset-builder owner (served mix and
  eval-coverage guard), eval owner (three-seed protocol and per-speaker
  MSE breakdown), and model owner (the capacity claim).
- 05 codebook reset: periodic dead-code reset (Razavi, van den Oord &
  Vinyals, VQ-VAE-2, NeurIPS 2019) closes the seed-dependent gap — 64/64
  codes in every seed (vs 18/63/32), margins tightening from 4.3%-38.2% to
  33.8%-37.6%, reset logs 1,893/1,848/1,388 per run tapering as the
  codebook stabilizes; the trade is that the reset eliminates dead codes,
  not that it produces a uniform codebook (entropy stays 0.79-0.83), and
  only half of VQ-VAE-2's fix was tested (EMA deliberately excluded so the
  two mechanisms could not be confounded); ownership split across codec
  owner (reset mechanism and threshold contract), eval owner (before/after
  read with only the quantizer changed), and mission owner (the
  maintenance-cost boundary).
- 06 which mechanism did it: the 2x2 factorial (reset x EMA, all four
  cells, three seeds) with corner-reproduction checks anchoring the new
  cells to the published numbers (plain reproduces stage 04, reset-only
  reproduces stage 05 to full float) — ema-only collapses the codebook to
  1/64 and lands worse than silence on every seed, and EMA's effect flips
  sign between the two halves of the grid (-0.405/-0.760/-0.644 without
  reset, +0.108/+0.058/+0.084 with); the trade is that the answer is
  mechanism identity, not hyperparameters — one value each was tried, and
  the quality effect of EMA on top of reset contains zero and is reported
  as inconclusive; ownership split across codec owner (factorial harness
  and corner reproduction), eval owner (three-seed main-effects protocol),
  and report owner (scoped conclusion).

The detours complete the same contract with their own measured reads:
seed-dependence as a measured property at the frontier (18/63/32 of 64
codes, entropy 0.405/0.760/0.644, MSE 0.02712/0.01698/0.02122, and the
realtime contract met on the worst seed, not the average); the fix's
generalization boundary (the stage-03 recipe holds where the data was
narrow and fails where it was not); the reset trajectory priced as the
cost view (1,893/1,848/1,388 resets, the first event reviving 60-63/64
codes at step 50, then ~240-248 per 200-step window until the final ~400
steps go quiet); the factorial corners reproduced bit-for-bit at ~74
minutes per seed (3.68 hours of process time, with the ema-only cell the
arm a two-arm study would have omitted); and the tail read that
redirects the optimization (a 4.4x p95/p50 the realtime budget must
absorb, where the cache keeps decode flat and the lever is network-side).
Citations carried by the chapters: van den Oord et al., NeurIPS 2017
(VQ-VAE); Razavi et al., NeurIPS 2019 (VQ-VAE-2 reset); Zeghidour et al.,
2021 (SoundStream); Défossez et al., 2022 (EnCodec); Kumar et al., 2023
(DAC); Yu et al., 2022 (Orca); Kwon et al., 2023 (PagedAttention/vLLM);
Panayotov et al., ICASSP 2015 (LibriSpeech); ESPnet category-power
sampler; Google ASR fairness, arXiv:2207.11345, 2022.

### Game AI — 00-06

**Status: done (fourteenth audit increment, 2026-08-08).**

Every stage 00-06 and every detour now carries the fix-and-trade and
who-owns-the-loop sections the audit contract requires, reusing the
mission's measured numbers (no new runs):

- 00 gridworld baselines: the baseline pair is the fix — random (0.222) is
  the no-learning floor and greedy one-step (0.824) is the beatable bar
  whose no-memory wall trap is documented, not hidden; the trade is that
  beating greedy is a weak claim by design, and a saturated or near-zero
  baseline would erase the space a trained policy must earn; ownership
  split across baseline owner (frozen 500-trial protocol), environment
  owner (BFS-rejection solvability), and evaluation owner (documented
  trap keeps the comparison fair).
- 01 grpo: the collapse is localized, not fixed — format credit is earned
  without the goal, so greedy argmax ignores the board (6.2-7.8%, below
  the 22.2% random floor) while sampled decode carries board signal
  (14.4-21.0%); the trade is the greedy-vs-sampled gap itself, the
  training metric and the serving metric diverging; ownership split
  across RL team (both decode modes reported), reward owner (reward
  shape is the suspect), evaluation owner (baselines that make "worse
  than random" visible).
- 02 report: the margin-vs-spread rule is the fix — greedy loses to random
  decisively (-0.1493 vs 0.016 spread), sampled is within noise (-0.0433
  vs 0.066); the trade is that small real effects are reported as noise
  by design, and NOT MET is paired with the failure catalogue so the
  verdict carries the mechanism; ownership split across report owner
  (mechanical verdict from committed JSONs), RL team (seed spread as the
  honesty unit), mission owner (the two-disjunct acceptance bar).
- 03 fixing collapse: two interventions tried and priced — smaller groups
  regress everything (degenerate steps 4-18/200, single-character
  completions strictly worse than baseline) and an entropy bonus raises
  mid-training entropy (1.3-1.7 nats) without moving the argmax; the
  trade is the sweep's honesty — a null covers only the cells run, and
  the diversity-direction detour (group 16: greedy 0.078 to 0.156,
  one seed) is where the mechanism moved; ownership split across RL team
  (greedy metric is the acceptance rule), reward owner (the reward shape
  is the wall), evaluation owner (per-configuration comparability).
- 04 minigrid: the solvability gate is the fix (hand-scripted 9-action
  sequence and wall-following 500/500 before training), and the
  interleaved masked-loss rollout buys honest partial-observability at a
  maintenance tax; the trade is that the gate proves learnability by some
  policy, not by GRPO's cold start — the 0.4% random floor is the
  mechanism behind 80/80 degenerate steps, not an environment bug;
  ownership split across environment owner (solvability contract), RL
  team (masked-loss verification against canonical `grpo_loss`),
  evaluation owner (cold-start attribution).
- 05 report: the elevation rule turns the repeated two-environment null
  into MET-as-null — grid-world alone was NOT MET, adding MiniGrid's
  total cold start makes the pattern the acceptance bar's second disjunct
  accepts; the trade is that the null is a deliverable only with rigor
  (committed JSONs, mechanical reads) and remains a boundary statement,
  never a win; ownership split across report owner (verdict prints the
  "honest null" qualifier), mission owner (two-disjunct bar applied as
  written), stage owners (artifacts the chain depends on).
- 06 tool-use rl: the protocol fix (word decisions to single characters
  `A`/`T`) is what unblocked training — the word version was 200/200
  degenerate because a cold policy never spells a 4-6 character sequence
  — and the format/outcome reward split is the standing trade (format
  credit is the scaffold, and the lever on 2-of-3 seeds refusing the tool
  is its balance); seed 0 matches the oracle at all 5 levels while seeds
  1-2 collapse, and the spread (0.1408) exceeding both baseline margins
  is reported as the honest third outcome; ownership split across
  task/reward owner (protocol and credit split), RL team (per-seed spread
  as acceptance), evaluation owner (baselines that define the headroom:
  0.8654/0.9000/0.9780).

### Multimodal generation — video path (codebook-collapse row)

**Status: done (thirteenth audit increment, 2026-08-08).**

The video path's codebook-collapse row now satisfies the contract: stage
01's tokenizer chapter and both of its detours carry the fix-and-trade and
who-owns-the-loop sections, reusing the mission's measured numbers (no new
runs):

- 01 video tokenizer: the three failure modes the queue named — codebook
  collapse, dead-code entrenchment, and decoder saturation — each open
  with the operational symptom (all three plateaued at the same flat
  baseline, invisible to the aggregate loss), each fix names its trade
  (data-seeded init assumes output-scale stability, the 20-step revive
  steers the codebook by the current batch and leaves seed dependence
  behind, removing the final `Tanh` moves clamping to export time), and
  the diagnostic-cost trade is explicit: the three fixes do not
  interchange, and finding them required per-mechanism probes
  (single-clip overfit control, direct decoder inspection). Ownership
  split: codec owner holds the three mechanisms and end-of-training
  codebook health as the contract, data pipeline owner owns the corpus
  imbalance that makes saturation the fastest early win, model team
  inherits the vocabulary the codec serves (15/64 no-revival collapse
  silently shrinks it and is invisible from the downstream loss).
- when-the-dead-codes-revive: the revive loop's trade is stability for
  utilization (158 revived codes prove the loop worked; an aggressive
  schedule disrupts a healthy codebook, a stale one revives nothing);
  the codec owner owns the schedule as a frozen contract and the
  token-contract detour owns the residual seed dependence.
- what-a-video-token-is: seed-dependence measured (63/64 vs 49/64, quality
  tracking usage 0.0788 vs 0.0885), the aggregate-beats-baseline read
  called out as the trap, and ownership split across codec (health
  contract per seed), evaluation (two-baseline comparison), and model
  team (inherits the vocabulary).

### Bio-pharma modeling — 00-06

**Status: done (fifteenth audit increment, 2026-08-08).**

Every stage 00-06 and every detour now carries the fix-and-trade and
who-owns-the-loop sections the audit contract requires, reusing the
mission's measured numbers (no new runs, no new model calls). The named
queue row is the scarcity-driven verdict loop — how a mission keeps an
honest verdict when the data is the problem:

- 00 dataset and property: the scaffold split that measures both axes —
  leak (overlap 0.0, verified) and balance shift (train 14.8% vs test
  19.7% positive on SR-MMP) — and the 12-endpoint balance detour that
  names the 15.8%-positive panel and the 5,810 labeled compounds; the
  trade is that a leak-free split can still move the minority class, so
  overlap and balance are reported as separate properties, never merged;
  ownership split across dataset owner (split construction and both
  numbers), model owner (inherits the shift), and mission owner (the
  split's generalization claim). Citations: Hansch & Fujita 1964; Bemis &
  Murcko 1996; Wu et al. 2018 (12-task random-split means 0.822 KernelSVM
  / 0.829 GC; per-endpoint ~0.90 refused as unverifiable).
- 01 descriptor baseline and model: the two-arms comparison with seed
  spreads reported per arm (descriptors 0.8142 ±0.0010 vs SMILES
  transformer 0.7312 ±0.0159; model 696,065 params vs ~10); the trade is
  that a single seed cannot separate signal from noise, so the verdict
  rule is spread-relative by contract; ownership split across eval
  (seed protocol), representation owner (the arms), and report (the
  verdict bar).
- 02 report: the itemized acceptance table that separates discipline from
  outcome — three of four items hold while the headline is NOT MET (gap
  0.0830, 5x the 0.0159 spread) — and the baseline-refuses-to-lose
  detour that reads a decisive loss instead of a near-tie; the trade is
  that itemization invites a "three of four" softening, resisted by
  naming the headline first; ownership split across report (headline-first
  structure), dataset (measured 0.0 overlap), and mission (double-stated
  does_not_prove).
- 03 second endpoint: the scarcest endpoint's split shift (NR-PPAR-gamma:
  2.29% train vs 5.28% test positive, 2.3x; 118 train positives) and the
  INCONCLUSIVE verdict (model 0.6591 vs descriptors 0.6554, gap 1/17th of
  the model's 0.0620 spread); the trade is the declared no-result rule,
  which costs a nominal lead to keep the verdict seed-proof; ownership
  split across mission (the declared bar, written before training), model
  (seed protocol), and report (no-result as a real result, with the
  118-vs-689 count as the measurable cause).
- 04 third endpoint: the mid-range point that separates the two claims —
  NR-ER (12.8% positive, 628 train positives) gives the model its first
  clean win (0.6679 vs 0.6413, margin 0.0265 clearing the 0.0227 spread;
  corrected counts 118/689 and monotone spreads 0.0620/0.0227/0.0159);
  the trade is that the win is endpoint-specific, never a general "the
  model got better"; ownership split across mission (deliberate midpoint
  selection), eval (win-beyond-spread bar), and report (scoped framing).
- 05 cross-endpoint analysis: the directional n=3 read that records
  variance-vs-scarcity as monotonic (118 -> 0.0620, 628 -> 0.0227, 689 ->
  0.0159) and win/loss-vs-scarcity as not, refusing to compute a
  correlation; the trade is the ceiling — a legible pattern, not a fitted
  claim, and explicitly not a law; ownership split across analysis (n=3
  ceiling), dataset (positive counts from split records), and report
  (scoped conclusion).
- 06 model or representation: the RDKit-agreement check (Tanimoto
  Spearman 0.9012, mean difference 0.0171, 0/60 bit-identical) that
  validates the from-scratch fingerprint so the representation finding is
  about representations, and the width sweep that measures the
  memorization knee (test AUC peaks at 256 bits 0.713, gap grows
  monotonically 0.122 to 0.346 at 2,048; fingerprint loses everywhere on
  SR-MMP 0.6534 vs 0.8142); the trade is rank agreement over bit equality,
  and a per-endpoint knee that transfers nowhere without re-running;
  ownership split across representation (implementation and agreement
  record), eval (per-endpoint caveat), and report (the "wider is not
  better" headline, scoped to the representation family).

### Autonomous driving — 00-06

**Status: done (sixteenth audit increment, 2026-08-08).**

Every stage 00-06 now carries the fix-and-trade and who-owns-the-loop
sections the audit contract requires, reusing the mission's measured
numbers (no new runs, no new model calls). The named queue rows are the
three failure modes the mission exists to measure — perception failure,
distribution shift, and closed-loop evaluation:

- 00 scenario simulator: the episode contract plus disjoint-seed
  generation (train seeds 0-99, eval 100-149, checked programmatically),
  so a policy that memorizes tracks is caught by the eval split; the trade
  is that the determinism that makes everything scoreable is bought with a
  declared omission (obstacle speed `vx` is schematized but static — the
  collision check and render use fixed positions); the 0.002s generation
  and the 0.8 obstacle-pixel figure are the numbers every later stage
  reads; ownership split across simulator (episode contract and seed
  ranges), eval (inherits the split), and render (the sparsity stage 01
  exploits).
- 01 perception baseline: the information-leak measurement with a hand
  estimator as the honest baseline — learned lateral offset is 8x better
  (0.072m vs 0.588m) and obstacle distance 14x worse (6.526m vs 0.469m)
  because the render carries 0.8 obstacle pixels per frame; the trade is
  an open-loop MAE that can disagree with closed-loop driving, and the
  fix buys correct attribution — a policy blamed for failing avoidance
  would be blamed for a boundary the render set; ownership split across
  perception (the estimators and the MAE protocol), render (sparsity), and
  downstream policy (inherits the boundary: densify the render or use
  state).
- 02 expert policy: the ceiling-and-floor pair from the same controller
  (expert 0.92/0.08 vs lane-only floor 0.28/0.72), isolating the 0.64 gap
  imitation must earn; the trade is that the expert sees true state, so it
  does not demonstrate avoidance is learnable from the render, and its
  four sandwich failures are the honest upper bound; ownership split
  across expert (controller mechanisms and the stated sandwich mode), eval
  (identical-scenario protocol), and mission (the minus-avoidance floor
  contract).
- 03 behavior cloning: the majority-action baseline (steer 0.883 vs 0.740)
  plus open-loop-first ordering, with the joint figure 0.772 exposed as
  hiding the dodge-frame minority; the trade is an open-loop metric that
  rewards reproducing the dominant action, which is why the artifact
  trained here is the exact one evaluated in the loop next; ownership
  split across clone (demos and architecture), eval (majority baseline and
  held-out frames), and report (the same-weights handoff to stage 04).
- 04 closed-loop eval: in-loop evaluation on identical scenarios with
  floor and ceiling beside the learner, imitation accuracy reported beside
  completion on purpose — 0.77 joint accuracy collapses to 0.28
  completion, statistically indistinguishable from the floor (0.28, 0.72,
  mean x 35.2), and the declared verdict is NOT MET, reported rather than
  tuned away; ownership split across eval (identical-scenario harness),
  model (the same weights, no retraining), and mission (the acceptance
  criterion and the declared next rung: weighted/labeled losses, then
  DAgger-style on-policy querying, neither run here).
- 05 harder scenarios: the hard split declared before the run and never
  tuned against (curvature 0.3-0.7 to 0.9-1.4m, wavelength 14-22 to 9-13m,
  obstacles 2-4 to 4-6, seeds 200-249); the boundary breaks on both sides —
  expert 0.92 to 0.78, clone to 0.04 with a 0.72 timeout — and the speed
  dimension is declared but not integrated, so the shift is a boundary of
  this generator, not of real road geometry; ownership split across
  scenario (frozen hard settings), eval (identical tracks), and report
  (boundary-as-finding either way).
- 06 report: a report that reads only the runs/ JSON files and renders
  verdicts against the declared acceptance criteria — the five-row table
  (0.28/0.92/0.28/0.78/0.04) beside the four-MET/one-NOT-MET verdict list,
  with the imitation-vs-loop gap (0.77 vs 0.28) and does_not_prove stated
  beside the numbers; the trade is that itemization separates discipline
  from outcome, so the NOT MET headline stands plainly; ownership split
  across report (reading-only verdict contract), stage owners (runs/
  records), and mission (does_not_prove and the acceptance criteria).

### Quantitative research — 00-05

**Status: done (eleventh audit increment, 2026-08-08).**

Every detour in stages 00-05 now satisfies the contract's fix-and-trade
and who-owns-the-loop halves: each carries a `## The fix and its trade`
and a `## Who owns the loop` section before its evidence boundary, reuses
its own measured numbers (no new runs), and cites dated sources:

- 00 market data: the as-of join and the restatement gap — the naive join
  is wrong on 4% of 69 AAPL fiscal periods (mean error 1.65%, the 2017
  error 3.8% of equity), a look-ahead that looks like a measurement error
  until the filing dates are on the join key; fix is the filing-date join
  plus the corporate-action reconstruction as a sanity check, trading
  freshness (an as-of panel deliberately lags the newest restatement) for
  correctness; ownership split across the data owner (the availability
  timestamp), the research platform (the join), and the strategy that
  inherits the panel; Elton, Gruber & Blake, RFS 1996, and the
  point-in-time database as a commercial category (Compustat).
- 01 signal research: the search that inflates its own winner — 32
  candidates, best in-sample IC 0.0947, 95 of 300 permutations match it,
  and at 1,024 candidates pure noise beats it in all 200 replicates; fix
  is the disclosed search log plus the best-of-N null curve, trading
  power for false-positive control, with the effective-trial denominator
  unobservable (correlated variants over-correct, families under-correct);
  ownership split across research (the log), statistics/evaluation (the
  null and the deflation), and stage 03 (the consumption); Bailey & López
  de Prado, "The Deflated Sharpe Ratio," 2014; Harvey & Liu,
  "Backtesting," 2015.
- 02 cross-sectional rank: the sizing rule that is the strategy (four
  rules: HHI 0.6667 to 0.1776, paper Sharpe -0.68 to -1.20) and the cap
  that re-breaks itself (7 to 47 violations under sequential
  cap-then-de-mean; the cap binds below 0.25, trades exposure for
  diversification, and taxes tightness); fix is the joint constrained
  optimizer, trading transparency and speed for constraint correctness;
  ownership split across research (the rule), portfolio construction (the
  constraint pipeline), and risk (the cap policy and its violation check).
- 03 walk-forward validation: fold-specific fit that is not strategy fit
  (in-fold 0.47-1.40 vs out-of-fold -1.06-3.74; boundary rows a different
  regime in both label widths) and the negative result that is still the
  lesson (three paths: 0.7393 / 0.9722 / 0.9722); fix is purge and
  embargo with the boundary partition as the case-finding step, trading
  usable rows for leak-freedom (López de Prado, *Advances in Financial
  Machine Learning*, Wiley, 2018); ownership split across the backtest
  platform (the eligibility boundary), research (the label definition and
  information lag), and statistics/evaluation (the deflated out-of-fold
  read).
- 04 cost and capacity: the two ceilings that are different — liquidity
  (USD 25bn discrete-sweep peak) vs cost (USD 125bn breakeven) — and the
  cliff where participation crosses 100% (net-dollar peak USD 31.6B /
  USD 1.46B/yr, negative at USD 100B); fix is the pre-trade capacity
  screen and the capacity curve, trading measured ADV and volatility
  against declared spread, commission, and impact assumptions whose
  coefficient must be fitted from the firm's own fills; ownership split
  across capacity/risk (the screen and its assumptions), execution (the
  fills that re-fit impact), and research (the paper return); Almgren,
  Thum, Hauptmann & Li, "Direct Estimation of Equity Market Impact,"
  2005; Tóth et al., "Anomalous Price Impact," 2011.
- 05 report: the three-way verdict and the refusal that names everything
  (CANNOT DETERMINE with 18 named missing inputs — the acceptance
  contract enumerated); fix is the grouped refusal plus the integrated
  outcome artifact that turns it into MET or NOT MET, trading momentum
  (no verdict, no decision) for honesty; ownership split across the
  report/release owner (the verdict contract and the integrated
  artifact), each stage owner (its named inputs), and the reader; the
  deflated-Sharpe input among the 18 carries Bailey & López de Prado,
  "The Deflated Sharpe Ratio," 2014, and Harvey & Liu, "Backtesting,"
  2015.

### Agentic platform — 00-06

**Status: done (twelfth audit increment, 2026-08-08).**

Every stage 00-06 and every detour now carries the fix-and-trade and
who-owns-the-loop sections the audit contract requires, reusing the
mission's measured numbers (no new runs, no new model calls):

- 00 task set: the admission rule (fail-at-base/pass-at-gold) plus the
  three-outcome pytest handling that stops "nothing ran" from reading as
  "failed"; trade is yield for integrity — 2 of 4 private and 2 of 6
  public candidates survive (0.08% of history), and a task set is
  defined by its exclusions; ownership split across the benchmark owner
  (the rule and the verify runs), the routing owner (inherits the
  distribution), and the report owner (never-pooled public/private
  separation); mutation testing (DeMillo, Lipton, Sayward 1978) and
  SWE-bench (Jimenez et al., 2023).
- 01 no harness: the blind-call control with oracle file location; the
  trade is that it measures "can fix once told where," not "can find the
  bug," and its failure view is distorted by design (11 of 12
  non-resolving attempts never applied; sonnet's no-harness arm costs
  more per success than the harness, \$1.3744 vs \$0.5369); ownership
  split across benchmark (the oracle concession), harness (the
  comparison), and routing (cost-per-resolved floor).
- 02 agent loop: the three-check scorer with the diff guardrail first —
  process supervision in the Uesato et al. (2022) sense — plus
  base-state freeze, JUnit XML, and the no_tests_ran verdict; the trade
  is that the guardrail refuses legitimate test edits to stay honest;
  ownership split across harness (scorer and verdict contract), task-set
  (baseline capture), and model team (inherits the verdict; "never
  fired" is a reported outcome, not a gap).
- 03 cheap or expensive: the metric pair (resolve rate beside dollars
  per resolved) plus the patch-generality probe; the trade is that the
  probe carries the quality axis resolve cannot see — haiku 6/6 resolve
  with 0/3 generality (1.2e-03/4.2e-02/1.2e-03 errors) versus 3/3 for
  sonnet and opus — and cost-optimal and latency-optimal are different
  policies; ownership split across routing (tier policy), eval (the
  probe), and model team (dated aliases, "latent, not live" boundary).
- 04 how it fails: the per-category failure taxonomy; the trade is that
  the zero-failure harness row is a property of this task set, and the
  tamper guardrail's zero real firings are reported as "never fired"
  rather than engineered; ownership split across harness (category
  contract), task-set (difficulty distribution), and report
  (explicit-or-fired boundary).
- 05 report: a report that computes — report.py reads committed runs/
  records and renders MET/PARTIAL/NOT MET per acceptance bullet; the
  trade is that PARTIAL is a decision cost, and bullet 1 names its own
  gap (the public set has no no-harness control; the opus margin sits
  inside spread), with the scope substitution carried forward, not
  erased; ownership split across report/release (verdict contract),
  stage owners (runs/ records), and the maintainer (the routing decision
  the report feeds but does not make).
- 06 closing the loop: the outcome-feedback retry (Reflexion, Shinn et
  al. 2023; Self-Refine, Madaan et al. 2023; RLEF, Gehring et al. 2024);
  the trade is priced per turn — \$0.254 per attempt, 2/12 resolved,
  bimodal (applied and resolved coincide; 10 of 12 corrected diffs still
  rejected, haiku 0/6); ownership split across harness (retry semantics
  and base-state reset), eval (per-tier attribution), and training/data
  (the interpretation boundary: a prompt-level demonstration, not
  accumulated agentic training data — which the LLM mission's mix and
  recovery chapters measure separately).

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
