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

**Status: in progress (search mainline 10-13, advanced 19-24, and
frontier 35-37 audited, 2026-08-07; this track is complete).**

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

**Status: pending.**

Audit auction, eCPM ranking, calibration, pacing, externality, frequency
capping, creative selection, bid strategy, auction revenue, RTB pipeline, ads
measurement, interleaving, first-price transition, privacy-safe attribution,
LLM creative generation, marketplace economics, advertiser ROAS. Ads is where
the A/B and traffic-split detail belongs most.

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

- 64 AUC-label seesaw: a shared-trunk run over 2,560 rows (naive shared
  bottom, slice-weighted, gated MMoE-lite; click 0.726/0.723/0.725, buy
  0.716/0.781/0.653) reframed as the multi-objective decision: the same
  table ships different models under two declared contracts (buy-primary
  picks slice-weighted; click-primary blocks gated on the buy 0.653
  guardrail) — the objective contract, not the model, is the decision.
  The stratified audit stays as eval rigor (aggregate "flat" -0.003 click
  is head 0.644 to 0.630 paying and tail 0.662 to 0.706 gaining), and the
  calibration axis is moved out of the main path into its detour (slope
  1.188; temperature scaling 1.098 to 0.983). Ownership split across
  product (frontier position), evaluation (per-objective gate), model
  (structure and weight dial); seesaw term and fix cited to PLE (Tang et
  al., RecSys 2020) and MMoE (Ma et al., KDD 2018). Detours unchanged:
  the weight dial, gradient surgery (43/60 conflicting epochs yet PCGrad
  neutral), and the calibration layer as a separate contract.
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

**Status: in progress (00-corpus data health, 02-pretrain divergence,
03-sft template contract audited, 2026-08-07).**

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
