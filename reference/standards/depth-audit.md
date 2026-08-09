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

**Status: done (first audit increment, 2026-08-07; structural re-check
2026-08-08; interactive wiring 2026-08-09).**

Re-checked 2026-08-08: all 24 chapters now carry `## The fix and its trade`
and `## Who owns the loop` before their evidence boundary, the trade named
with the measured number, and the ownership split per stage (which team
owns the label, the cut, the traffic, the retrain).

Failure modes audited with measured runs: entire-space funnel (CTCVR under
sparse CTR), delayed feedback (freshness vs correctness, window size),
negative sampling (calibration vs ranking, ratio misestimation, extreme
negative rates), exposure bias (IPS vs naive, thin exploration traffic, noisy
propensity), heavy-tail objectives (AOV skew, whale dominance), multi-task
conflict (gradient balancing, gating, dominant-task drift), funnel consistency
(impossible probabilities, constraint cost, order vs click), cascade
consistency (pre-rank vs final ranker, distillation blur, top-k preservation).
On 2026-08-09 each stage without an interactive received one ProcessDiagram
wired to its recorded run: entire-space funnel (0.735 vs 0.740, censored
0.448 vs 0.618), negative sampling (AUC flat 0.659, ECE 0.473 to 0.017),
exposure bias (0.874 to 0.962 to 0.995, noisy 0.376), heavy-tail objectives
(1.409/21.2% to 1.045/5.2% to 1.290), funnel consistency (0.672/649
violations to 0.501/0), cascade consistency (0.35 to 1.00 top-20 recall).

### Personalized discovery — shared 00-09 (retrieval to report)

**Status: done (second audit increment, 2026-08-07; structural re-check
2026-08-08).**

Re-checked 2026-08-08 across all 10 stages — 40 chapters (10 parents and
30 detours): every chapter now carries `## The fix and its trade` (the
failure named first, the measured trade named) and `## Who owns the loop`
(cross-team handoffs per stage) before its evidence boundary. Stage
numbers are reused verbatim from the recorded runs: pre-rank surface
0.000 long-tail vs 0.100-0.400 overall; fine-rank weighted transfer
recovering dwell -0.080 to 0.809; value-tree multiplicative flip at 0.165
vs additive 0.410; mixing cap 2.2624 vs penalty 2.1853 and the ad knee at
revenue/displaced 1.12 to 0.93; rule-engine EU+safety joint empty set;
serving p95-sum 54.74 vs measured 49.31; report guardrail veto 0.271 vs
0.298 with a 0.4102 headline still NOT MET.

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

**Status: done (third audit increment, 2026-08-07; interactive wiring
2026-08-09 for stages 43, 44, 45, 47, 54, 55).**

On 2026-08-09 stage 54 received a ProcessDiagram wired to its recorded
fixtures: the validity gate (broken SRM chi2=21.52 p=3.51e-06 vs fixed
chi2=0.04 p=0.832, unit-mismatch SE gap 3.19x, SRM firing at ~2,000 users
against 78,000 for outcome power, 24% unit-mismatch false positives and
53% switchback per-minute false positives).

On 2026-08-09 stages 43, 44, 45, 47, and 55 each received a ProcessDiagram
wired to the recorded runs: feature store (store scores 17.5/-2.5/11.5 at
0h vs naive 12.5/-5.5/7.5 at 3-5h, reordering P1002/P1001), training-
serving skew (offline P1001,P1002,P1003 vs live P1003,P1001,P1002),
feedback loops (head 99% vs tail 0% impression share, sustained exposure
5/20), monitoring and drift (predicted 0.040 flat vs observed falling to
0.020, ALERT at hour 10), and LTV/CAC (organic 6.08, referral 1.80, paid
0.94; 1m-to-24m window curves deciding the channel verdict).

On 2026-08-09 (second shared wiring pass) stages 46, 48, 49, 50, 51, 52,
and 53 each received a ProcessDiagram wired to the recorded runs:
retraining/staleness (snapshot ages 0 to 5 to 6 wrong pairs by hour 12;
volatile cohort due first), realtime user state (session boost lifts audio
0.032 to 0.041; depth-1 sessions own 70% of traffic at 58% of the blended
lift share; p95 38ms to 118ms), throughput/capacity (p99 933ms and 68.8%
over deadline at 55 req/s; p95 150ms already exceeds the 100ms deadline;
hedge cuts 18.5% to 3.4%), cost per query (4.0 units per query vs 200,000
exhaustive; recall owns 25% of budget at 10M and 68% at 1B), new-user
experience (NDCG 0.122 popularity to 0.878 after 20 interactions; wrong
prior 0.000 at 0.18 retention below no-ask 0.20), trust/explainability
(largest term 47% unverifiable; similar-users surface 70% uncheckable
headline vs 62% aggregate), and fairness/allocation (10% floor lands at
9.2% served; first ten points cost 0.0021 aggregate CTR).

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

**Structural re-check 2026-08-08 (thirty-fourth audit increment):** a
fresh scan found the prior "done" claim repeated the ads pattern — the
parents passed who-owns but carried no fix-and-trade section. Closed
now, each reusing the chapter's own measured numbers. 43 feature
store's fix is freezing each feature at ingestion and serving that
frozen value to both sides, priced by the executed read — the naive
path reorders P1002 past P1001 (17.5 vs 12.5) on a feature the model
never saw, and the audit names the divergence per feature
(`age_hours` mean served-vs-trained +4.00, max +5.00, DIVERGENT);
traded against freshness, since a promo landing mid-hour is served
stale 22 of 24 hours on a daily refresh and zero hours on streaming
(Zipline, Strata 2018; Sculley et al. 2015). 44 training-serving
consistency's fix is the logged-versus-live distribution gate itself
(offline order P1001, P1002, P1003 vs live P1003, P1001, P1002; price
mean |live minus logged| 4.000, max 7.000, ctr 0.010 and 0.016,
DIVERGENT), traded against the fact that the gate only catches the
drift — the logging path, label window, and join are owned elsewhere
(TFX, KDD 2017; Breck et al. SysML 2019; Chapelle 2014). 45 feedback
loops' fix is exposure-aware measurement (head 99 percent vs tail 0
percent impression share, naive CTR 0.060 against true 0.030, IPS
recovering 0.030), traded against propensity noise — a stale
propensity estimate re-borrows the luck it was built to remove
(Mansoury et al. CIKM 2020; Chaney et al. RecSys 2018; Abdollahpouri
AIES 2019). 47 monitoring's fix is slice-aware drift detection — a
category at 6 percent of traffic collapses to 0.010 (gap 0.030) while
the aggregate 0.003 gap never fires, and the prediction-vs-observed
gap widens pred 0.040 to observed 0.020 with an EWMA alert at hour 10 —
traded against slice noise, since a 0.002 threshold fires at 7 hours
while the 500-per-day alert catches a 50 percent drop 3 days late
(Gama et al. 2014; Breck et al. 2019). 48 realtime's fix is
depth-aware freshness — the 70 percent shallow sessions earn lift
0.0066 (58 percent share) against 0.0118 at depth 4, blended 0.0079 —
traded against latency (p95 38 to 118ms, 20 of the reads blowing the
100ms deadline) and against the leaky feature that scores 300/300
offline where the as-of window scores 33/300 (Hidasi et al. ICLR
2016). 49 capacity's fix is load-shaped capacity planning — the p95 of
the mixed load exceeds the 100ms deadline at every offered load, 55
req/s runs p99 933ms with 68.8 percent over, and mean capacity 59
req/s is the divergence load, not the answer — traded against tail
hedging, which cuts the fanout-multiplied tail from 18.5 percent to
3.4 percent at 2x work (Dean & Barroso CACM 2013). 50 cost-per-query's
fix is the cascade with recall owned explicitly — 4.0 against 200,000
exhaustive (50,000x), recall 25 percent at 10M, 46 percent at 100M, 68
percent at 1B, cache at 90 percent hits taking the query to 0.44 —
traded against the tail that misses the cache: 30 percent of queries
pay the full 4.0 against a blended 1.91 (Han, Mao & Dally ICLR 2016).
51 new-user's fix is a calibrated prior plus a bounded explore budget —
popularity 0.122/0.24, the right prior 0.878/0.55, the confident wrong
prior 0.000/0.18 below the no-ask baseline 0.050/0.20, all hidden by
the aggregate 0.254 — traded against exploration as a tax on a short
runway (greedy 0.817, 10 percent epsilon minus 0.022, 30 percent minus
0.090; Abdullah et al. Applied Sciences 2021). 52 trust's fix is a
verifiable-headline design — similar-users leads with an uncheckable
claim on 47 percent of items (viewed-category 33, affinity 19; the
surface reaches 70 percent uncheckable against 62 percent aggregate),
and a 5 percent false rate roughly doubles opt-outs while 50 percent
drives one in seven to leave — traded against counterfactual
attribution that flips the headline (Zhang & Chen FTIR 2020). 53
fairness's fix is serving-side allocation with a renormalisation guard
— the declared 10 percent floor lands 9.2 percent served (+0.8), and
the gap grows with the floor (15 percent floor to 12.6 served), cost
measured at CTR 0.0355 to 0.0334 (0.0021), position-adjusted share
14 to 36 percent — traded against the constraint cost and the
definition-dependence that flips the verdict (Abdollahpouri et al.
KDD workshop 2020). 54 online-experiments' fix is the three-fixture
validity gate — SRM chi2 21.52, p 3.51e-06 on the drifted bucket
(corrected log chi2 0.04, p 0.832), unit-mismatch SE gap 3.19x, and
the switchback serial-dependence fixture — traded against power, since
clustered errors cost 24 percent false positives when skipped and the
per-minute switchback rejects 53 percent of nulls with a 1 percent
effect needing 36 years (Kohavi/Tang/Xu 2020; Fabijan et al. 2019;
Tang et al. 2010; Bojinov et al. 2023). 55 LTV/CAC's fix is
horizon-matched unit economics — the 5-month view ranks organic 6.08,
paid 0.94, referral 1.80, and the window decides the bet: 3 months
ranks paid above referral while 24 months reverses it (referral 11.78
vs 0.97), and a 35 percent retention floor moves LTV from \$27.54 to
\$50.83 — traded against the noise and action lag of the long horizon
(Fader, Hardie & Lee Marketing Science 2005; Gupta et al. JMR 2004).

**Structural re-check 2026-08-08 (thirty-fifth audit increment):** a
detour-level scan of the same range found all 36 detours missing the
fix-and-trade section, and all but the split-lies detour missing
who-owns (stage 46's three already carried both from the earlier pass).
Closed now, each reusing the detour's own measured numbers: the
feature-divergence detour's fix is the as-of read itself (train order
P1001, P1002, P1003 against serve order P1002, P1001, P1003) traded
against the feature owner's obligation to say how fast a value moves;
the missing-feature detour's fix is an explicit, auditable default
policy (the zero default promotes P1004 to rank 1 where the true \$39
price puts it at rank 2) traded against disqualifying fresh items
entirely; the online-value-moves detour's fix is a per-feature latency
class (1 stale hour on hourly refresh against 22 of 24 on daily)
traded against write cost, the same freshness decision stage 46 makes
for snapshots. The label-arrives-late detour's fix is a holdout window
(the hour-6 cut estimates P1002 and P1003 at 0.0000 against a true
0.0300) traded against volume and recency; the join-looks-ahead detour's
fix is the as-of join plus a temporal leak audit (label-time join
separates 1.00, as-of 0.00) traded against an offline number that
honesty makes look worse. The filter-bubble detour's fix is a per-user
diversity floor (33 to 94 percent liked-category share by epoch 10)
traded against precision; the popularity-collapse detour's fix is
exploration budgeted before the change (item 15 at 0.1 percent share
150 rounds after becoming best) traded against head efficiency; the
policy-borrows-luck detour's fix is policy-version-paired propensity
logging (IPS recovers 0.030 for both items, stale propensities
reproduce 0.060 and 0.015) traded against re-estimation cost. The
alert-is-noisy detour's fix is a threshold set on the measured noise
floor (+/-0.002 fires on three jitter hours, +/-0.010 loses the break
hour) traded against detection latency; the drift-is-silent detour's
fix is an online instrument that does not share the serving path
(NDCG flat 0.712 while observed CTR halves 0.039 to 0.020) traded
against serving-path plumbing; the slice-hides detour's fix is sample
size, not threshold (500/day fires twice on noise and detects 3 days
late; pooled detects day 23 with zero false alarms) traded against
latency. The session-leak detour's fix is the time-ordered join (leaky
300/300 top-1 against as-of 33/300) traded against an offline number
that looks worse; the realtime-is-too-expensive detour's fix is
latency-and-freshness accounting (20 features blow the 100ms deadline
at 118ms) traded against a line that moves with the deadline; the
session-state-moves detour's fix is a per-surface decay rate (boost
0.0097 at 2 minutes to 0.0002 at 40) traded against the mood that never
releases or the state that is decorative. The fanout-tails detour's fix
is query-level tail sizing with budgeted hedging (1.1 to 18.5 percent
over 500ms at fan-out 20, hedged 3.4) traded against 2x shard work;
the peak-arrives detour's fix is capacity against the arrival curve
(2x load pushes p99 to 11,850ms) traded against idle standby; the
tail-costs detour's fix is percentile sizing (mean capacity 59 req/s
misses 94.3 percent of deadlines) traded against idle headroom. The
cache-pays detour's fix is hit-rate-curve sizing (90 percent hits to
0.44 units) traded against staleness, stage 46's trade one level down;
the model-is-too-big detour's fix is cost-per-query pricing (0.013 NDCG
for 10M extra units a day) traded against opportunity cost; the
tail-misses detour's fix is candidate-budget cuts for cold queries
(blended 1.91 hides the 30 percent paying 4.0) traded against recall
misses on the cold tail. The personalization-scares detour's fix is a
bounded prior share (strong prior owns 40 percent of the page) traded
against the catalogue the user never sees; the bandit-explores detour's
fix is choosing where the exploration tax is paid (greedy 0.817
against 30 percent epsilon 0.728) traded against a shorter runway; the
user-is-new detour's fix is a falsifiable prior (right 0.878, wrong
0.000, below popularity 0.122) traded against the ask's own risk. The
attribution-shifts detour's fix is a named counterfactual (zero
baseline headlines "similar users bought", mean headlines "you viewed
this category") traded against the baseline's cost; the
explanation-is-wrong detour's fix is contribution, not coefficient
(largest weight +0.200 against largest contribution -0.0800) traded
against per-item computation; the trust-erodes detour's fix is gating
the feature on measured cost (5 percent false nearly doubles opt-outs)
traded against shipping fewer explanations. The constraint-bites
detour's fix is a floor at the measured knee (first 10 points cost
0.0021, next 10 cost 0.0027 per point) traded against aggregate CTR;
the groups-cross detour's fix is a named group before measurement
(mobile 8 percent against catalogue 10.1) traded against definition
complexity; the policy-is-biased detour's fix is position adjustment
before fairness (tail 14 to 36 percent exposure) traded against
re-estimation as the policy changes. The split-lies detour's gate is
the daily SRM check plus a declared-ratio config (corrected split p
0.858) traded against reruns of experiments that won while broken; the
user-crosses-groups detour's fix is the randomization-unit analysis
and washout (24 percent false positives at declared 5 percent; carryover
-0.072 to -0.005) traded against power; the traffic-is-two-sided
detour's fix is the unit chosen by interference strength (per-minute
53 percent false positives, 1 percent effect needing 36 years) traded
against the block unit's power. The cac-exceeds-ltv detour's fix is the
ratio gate (paid installs 0.94 against referral 3.06) traded against
capping a channel whose cohort the window has not fully seen; the
retention-flattens detour's fix is the floor as the LTV lever (35
percent floor nearly doubles \$27.54 to \$50.83) traded against the
measurement lag of retention work; the retention-window-truncates
detour's fix is per-horizon reporting and curve modeling (referral 0.78
at 3 months against 11.78 at 24) traded against the cost of modeling
the ramp and tail. Every detour in 43-55 now satisfies the audit
contract at the parent and detour level.

### Personalized discovery — search 10-24, 35-38

**Status: done (search mainline 10-13, advanced 19-24, and frontier
35-38, 2026-08-07/08; frontier chapter 38-conversational-surface audited
2026-08-08 and relocated from the shared 10-frontier directory to the
surface that owns it).**

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

### Personalized discovery — ads 14-18, 25-30, 38-43, 56

**Status: done for 14-18, 25-30, and 38-43/56 (fourth, seventh, and
eighth audit increments, 2026-08-07/08; frontier chapter
43-ads-inside-the-loop audited 2026-08-08 and relocated from the shared
10-frontier directory to the surface that owns it; 54-advertiser-roas
renumbered to 56 so it no longer collides with shared 54-online-experiments;
interactive wiring 2026-08-09 for stages 14, 16, 17, 30).**

On 2026-08-09 stages 14, 16, 17, and 30 each received a ProcessDiagram
wired to the recorded runs: ad auction (0.6118 with four bidders vs
0.2514 with one, reserve-binding 100% at one bidder), CTR calibration
(aggregate ECE 0.0238 passing vs mobile slice 0.2303 at 0.268 observed
against 0.498 predicted), budget pacing (naive exhausts at hour 3; cap
1.50 fully spent with 3 dark hours vs paced 88.4 of 100 and none), and
ads measurement (increment 0.4 points; p=1.000 at n=8,000; CI first
excludes zero at n=20,000; 80% power needs 28,547 per arm).

On 2026-08-09 (second ads wiring pass) the remaining 13 ads parents each
received a ProcessDiagram wired to their recorded runs: 15 eCPM ranking
(Ad B wins at 150.00; 7 of 18 perturbation cells flip the winner, 38.9%,
mean realized 136.11 vs optimal 150.00; 2-point pCTR change swaps the
winner), 18 ad externality (aggregate net +0.0688 vs engaged -0.3249 on
20,000 users), 25 frequency capping (CTR decays 0.050 to 0.002; aggregate
0.0328 hides power 0.0133 with 40.6% dead share), 26 creative selection
(greedy lifetime 635 clicks vs EWMA 828, Thompson 807 on 20,000
placements), 27 bid strategy (winner log CVR 0.0316 vs true 0.0188, bid
overpays 1.68x, IPW restores \$0.09), 28 auction revenue (first-price
round-1 0.7485 settles at 0.4980, 33% erosion), 29 RTB pipeline (p95
99.5ms fits, p99 108.2ms blows the 100ms deadline, 933 of 20,000 time
out), 38 interleaving (naive blend credits A 59.2% vs B 40.8%; random
start restores 49.7/50.3 at a 3.6% session cost), 39 first-price
transition (shading optimum \$0.50 nets \$0.25; belief error 0.3 costs
0.022, weaker-market mis-specification 0.100), 40 privacy-safe
attribution (epsilon 2.0 flips the close pair 12.9%, 81% over twelve
reports), 41 LLM creative generation (surface score misses CTR-best
55.1% at 7.3% mean loss; collapse cuts CTR 0.0911 to 0.0515), 42
marketplace economics (peak 35% / \$154; fixed 35% earns \$203 vs \$105
across the outer curves), and 56 advertiser ROAS (average clears 5.0 to
\$3,000 while marginal falls to 1.96).

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

Stages 38-43 and 56 now satisfy the same contract (eighth audit
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

**Structural re-check 2026-08-08:** all 68 ads detours now carry the
`## Who owns the loop` section before their evidence boundary, matching
the search and shared detour convention. Each detour-level ownership
split names the 2-3 teams whose handoff the detour's failure exposes,
reusing the parent stage's team names and the detour's own measured
numbers (the thin-market reserve-binding share, the 0.075 flip point,
the 3.6 percent interleaving session cost, the 28,547-user power
calculation, the 1.96x marginal dollar). With this, every stage in the
ads range satisfies the audit contract at the parent and detour level.

**Structural re-check 2026-08-08 (thirty-third audit increment):** a
fresh scan found the prior "done" claim passed the detours but missed
the parents — all 18 ads parents carried who-owns without the
fix-and-trade section. Closed now, each reusing the chapter's own
measured numbers, and the stale duplicated tails in stages 15-18 (a
second evidence-boundary / check-your-mental-model / next block left
behind by the earlier insert) were removed. 14 ad auction's fix is
bidder depth, not the rule (four bidders 0.6118 per auction against one
0.2514, reserve-binding share 100.0 to 3.1 percent), traded against the
reserve stopgap that humps at 0.2492 near reserve 0.50 and kills sales
when set too high (0.85 eliminates the second bidder). 15 eCPM
ranking's fix is calibrated pCTR, the stage-16 precondition, priced by
the 7-of-18 flip grid (realized 136.11 against 150.00, flips costing
30-50), traded against calibration's cost and expiry (stale factor
over-correcting to 0.3000) and the tie-break/reserve policy choices
that remain. 16 calibration's fix is per-slice monitoring plus a
per-slice correction (aggregate ECE 0.0238 passes while mobile 0.2303;
the 0.5505 factor drops ECE 0.2450 to 0.0000), traded against expiry —
the same factor over-corrects new traffic to 0.3000 — and the
ordering-versus-values split the ranking-conflict detour measures. 17
pacing's fix is feedback control re-pacing against live delivery,
priced by the sweep (multiplier 1.50 spends 100.0 but late-window
collapses to 0.0 with three dark hours), traded against oscillation
(gain 3.0 darkens six of twelve hours) and the tight cap that leaves
50.0 of 100 unspent. 18 externality's fix is the per-slice net-value
rule (aggregate +0.0688 passes while engaged -0.3249 against casual
+0.2000; mean 0.2307 hides P90/P99 0.9500), traded against the
experiments substitution requires and slot count as the decision
variable (0.60 displaced in 4 slots, 0.20 in 8). 25 frequency capping's
fix is per-segment caps on a stable counter (casual 7 / standard 3 /
power 2 cut 6,152 impressions losing zero casual clicks, where global
cap 3 sacrifices 28.5 casual clicks to save 7.3 power clicks), traded
against reach (10,000 users at cap 1 vs 1,000 at cap 10) and the
counter that 30 percent of users lose (6,167 extra impressions at
0.0139 vs 0.0400). 26 creative selection's fix is the recency-aware
estimator, not exploration (EWMA 828 and Thompson-decaying 807 clicks
against greedy 635 and epsilon-greedy 645), traded against recency's
stability cost and cold start's traffic price (epsilon 0.20 serves the
new creative 1,994 placements for 653 clicks). 27 bid strategy's fix is
the selection correction (IPW restores 0.0187 and the \$0.09 bid from a
winner's log that reads 0.0316 and overpays 1.68x; delay fit recovers
0.0197 from a 0.0096 under-read), traded against the data the
corrections need and the cap that trades reach for price (\$0.10 to
\$0.06 drops wins from 3/5 to 1/5). 28 auction revenue's fix is the
settled state, not the day-one read (0.4980 settled against 0.7485
naive, 33 percent erosion, day-one overstating by 57 percent), traded
against the transition weeks and the reserve's own optimum at \$0.8
(revenue 0.37). 29 RTB's fix is the tail budget and the cascade (p99
108.2ms blows the 100ms deadline with 933 of 20,000 timing out; cascade
cuts an 18.0 percent model timeout rate to 6.9), traded against cheap
fallback bids on 33.1 percent of the worst-tail requests and the 5
percent rate that leaves 50,000 of a million slots unfilled. 30 ads
measurement's fix is sizing for the effect before reading (the
0.4-point increment is invisible at 8,000 users per arm, CI first
excludes zero at 20,000, 80 percent power needs 28,547), traded against
the revenue and traffic a larger holdout defers and the attribution
shortcut that overcounts by 0.6. 38 interleaving's fix is the randomized
blend plus tie rule and pooled test (naive credits A 59.2 percent for
equal teams; random start restores 49.7/50.3), traded at a measured 3.6
percent more sessions against a bias 78 standard errors from 50/50 at
200,000 sessions. 39 first-price transition's fix is shading as a
probed, hedged prediction (belief error 0.3 costs 0.022 per auction;
100-trial probes wander the optimum to 0.60 for 0.011 against 0.001 at
1,000), traded against rationed probing and the forecast error that
reads \$0.95 settling at \$0.42. 40 privacy-safe attribution's fix is
epsilon set against the decision gap and the report coarsened to the
noise floor (12.9 percent flip rate at epsilon 2.0, 81 percent over
twelve reports, 0.0 percent at epsilon 5.0; six channels flip 87.6
percent vs 12.3 for three), traded against the shared privacy budget
that 100 reports dilute to epsilon 0.02 each. 41 LLM creative's fix is
the score calibrated on delivered CTR (surface score misses the
CTR-best on 55.1 percent of batches for 7.3 percent relative loss,
chosen 0.0848 vs best 0.0914), traded against the impressions the
calibration costs and the generator collapse that re-runs 59.8 percent
of delivery at 0.0406 within-flight decay. 42 marketplace economics'
fix is the measured volume response before pricing (fixed 35 percent
within 2.6 percent of the fitted peak but 16.0 percent below the
elastic peak; \$203 vs \$105 across the outer curves), traded against
the two-sided response that moves the peak from 31.0 to 21.0 percent
and the shared elasticity shape across reserve, ad load, and take rate.
54 ROAS's fix is deciding the budget at the margin (average 5.21x
against a marginal 1.96x; a top cut loses \$980 per \$500 where the
first increment loses \$2,604), traded against the incrementality
experiments the marginal number requires, which is why the average
report ships and the budget-moves detour prices the consequence. All 18
parents now satisfy the contract at both levels.

### Personalized discovery — recommendation 31-35 (frontier)

**Status: done (fifth audit increment, 2026-08-07; frontier chapter
35-verification-replaces-score audited 2026-08-08 and relocated from the
shared 10-frontier directory to the surface that owns it; interactive
wiring 2026-08-09 for stages 31-34).**

On 2026-08-09 stages 31-34 each received a ProcessDiagram wired to the
recorded audit: LLM ranking (pointwise d1..d5 vs listwise 4/5 positions
changed; tail swing 10/10 at displacement 1.040), recommendation RLHF
(Bradley-Terry total 2.19, weakest pair 1.17; tail flips 4/10 at margin
0.04), multimodal recall (cold retrievable 2/3; tail single-modality
100%), slate vs item evaluation (a wins 2.55 vs 2.10 on item sum, loses
3.06 vs 3.36 on slate value; tail flips 10/10).

Stages 31-35 now satisfy the contract, each with an executed case-finding
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

**Structural re-check 2026-08-08 (thirty-second audit increment):** a
fresh scan found both stage parents still missing the fix-and-trade
section and all six detours missing both sections, so the "done" claim
above was incomplete. Closed now, each reusing the chapter's own measured
numbers. 64 parent's fix is the pre-declared contract (primary metric
plus guardrails) that turns the seesaw's undecidable-after-the-run
numbers into pass/fail — the same table ships buy-weighted under one
contract (buy 0.716 to 0.781, click clearing 0.720) and nothing under
the other (expert-gated breaching at 0.653) — and the trade is the
structural price of one shared representation, moved by the weight dial
(cheap first steps, saturation around tail AUC 0.71), structure, or
gradient surgery, in that order. Its detours now name the failure and
fix each: gradient surgery is not justified by conflict frequency (43 of
60 conflicting epochs, PCGrad still within noise at 0.712/0.712 — the
test is validation-loss interference, Yu et al. NeurIPS 2020, CAGrad Liu
et al. NeurIPS 2021); calibration is a second model with a freshness cost
(temperature 0.85 moves slope 1.098 to 0.983, but the frozen T reads
intercept -0.106 after a shift against the fresh -0.009 — Guo et al. ICML
2017, plus the monitoring job and re-fit cadence); and the weight dial's
aggregate AUC is head-weighted (0.735 to 0.704 monotone while the tail
gains 0.654 to 0.708, first step buying +0.028 tail for -0.035 head).
65 parent's fix is the density report plus three priced layers — label
supply (window, surrogate, exposure; the 50-percent-after-24-hours
display fact, Chapelle et al. KDD 2014), structure (shared trunk 0.780
vs from-scratch 0.678), delay-aware training (Ktena et al. RecSys 2019,
Yasui et al. CIKM 2020) — with the cold-item gate held on the interval
([0.500, 0.957]) until labels can decide. Its detours now name the
failure and fix each: the interval only narrows with label supply (width
1.000 at k=2 to 0.517 at k=30 — a data decision, not a model one); the
surrogate buys ranking and sells probability meaning (0.0395 predicted
vs 0.0036 true, ~11x, true-label AUC 0.706 vs 0.756 — corrected by
re-weighting and calibration, not the label alone); and warm start is
source alignment, measured per slice (click trunk 0.659 loses to scratch
0.740, aligned head-slice buy 0.786 wins; Yi et al. RecSys 2019). All
eight chapters in the two stages now carry both sections.

### Language-model system — 00-07

**Status: done (fourth audit increment, 2026-08-07/08; interactive wiring
2026-08-09 for stage 07-eval).**

On 2026-08-09 stage 07-eval received a ProcessDiagram wired to its measured
report: perplexity 21.677 at context 1024 vs the 9.712-nat uniform
baseline, loglik 0.625 with CI [0.250, 0.875] at n=8, generate 0.050
plus or minus 0.100, agent 0.000 [0.000, 0.000], with the refusing report
format as the spine.

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

**Structural re-check 2026-08-08 (thirty-first audit increment):** a
fresh scan found six real chapters in this topic still missing both the
fix-and-trade and who-owns sections, despite the end-to-end claims above:
the tokenizer parent, the RL parent, the heavy-tail-waits rollout detour,
the agent parent, the eval parent, and the vision parent. Closed now, each
reusing the chapter's own measured numbers. 01-tokenizer: the fix is
byte-level BPE over the two lossy/too-long naive answers (252,259 unique
words in 9,025,172 total; no `<UNK>` possible), priced at 4.497
chars/token against the 14.4 percent of the 88M model's parameters the
vocabulary fixes, with the naive trainer's 2.4 s/merge replaced by the
indexed trainer and the 60,978-token export parity audit; ownership
split across tokenizer/model (the freeze), data pipeline (per-class
token ledger: English 0.24 vs CJK 2.96 vs emoji 4.00), serving/product
(the 4,096-token window is a 1,382-CJK-character window), and eval (the
divergence that only surfaces at stage 02 as non-convergence).
04-rl parent: the fix for the 200/200 degenerate-group run (probability
3e-12 per completion, expected count 2e-8 across 6,400 sampled) is the
warm start, traded against RL's inability to install zero-probability
behavior (game-ai: 14.4-21.0 percent under sampled decode, greedy
ignores the board), the KL leash's beta knob, and G-times generation
for the critic's memory; ownership split across RL/alignment, reward
and environment, training-infra/serving, and evaluation. The
heavy-tail-waits detour names the fix as the scheduling policy, not
more workers — async 1.73x at 2 workers to 1.30x at 8 on the same
40-trajectory list — with ownership split across training-infra (the
policy), sampler (the 80/20 tail), and evaluation (speedup without
worker count is not comparable). 06-agent parent: grounding closed by
the stop-sequence plus unconditional truncation pair, and the 0/6 real
run (an 88M checkpoint SFT'd on chat pairs never emitted one parseable
`Action:`) fixed by agentic trajectory composition, not prompting;
ownership split across harness/platform, data, security/infra, and
evaluation (the harness-disclosed trace). 07-eval parent: the fix is
the refusing report format — tokenizer sha256 and context length beside
the number, mandatory seeds, required baseline, harness block with
`harness_configs_seen == 1` — priced by its own reports (loglik 0.625
with CI [0.250, 0.875] at n=8; generate 0.050 plus or minus 0.100;
agent 0.000 [0.000, 0.000]; perplexity 21.677 at context 1024 against
the 9.712-nat uniform baseline); ownership split across evaluation,
harness, data, and product/release. Vision parent: the fix is the
two-baseline design — text-only (0.3270 vs vision 0.4375; shape_color
50.1 vs 27.2 percent) and hosted API (0.8329 at \$0.00128/question) —
plus the warmup that closed seed-2 collapse (spread 0.2309 to 0.0536);
ownership split across vision/research, data (116 pixel-identical
collisions, id-based real-photo guardrail), product/evaluation (NOT MET
is a buying decision), and platform (the CPU lane stages 04-05 ran on).
The two `prod/` pages under 06-agent are production-mapping tables with
no runs and no benchmark claims; they fall outside the failure-mode
contract, same as LANDSCAPE pages. The topic now scans clean apart from
the root README.

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

### Language-model system — vision path (00-06)

**Status: done (twentieth audit increment, 2026-08-08).**

Every stage 00-06 and every detour in the vision path now carries the
fix-and-trade and who-owns-the-loop sections the audit contract requires,
reusing the mission's measured numbers (no new runs, no new model calls),
and stages 04-06 — which previously carried no dated citations at all —
are now anchored:

- 00 task set: the leakage fix is widening the state space at the source
  (per-shape size and position jitter, 48 -> 3,600 single-shape outcomes)
  rather than patching with rejection sampling, which fixed the 116
  pixel-hash collisions and silently emptied eval's single-shape bucket
  (124 two-shape + 276 three-shape, zero one-shape) — a guardrail pass
  with a broken dataset; the trade is priced as the rejection burden (29
  today vs 507 in the recorded original), the 79/2000 train-internal
  duplicates disclosed, and the distribution check as a second gate;
  ownership split across data pipeline (generator and guardrail key),
  eval (post-fix distribution check), and model team (inherited eval
  properties); CCNet (Wenzek et al., 2019) and GPT-3 (Brown et al., 2020)
  as the production-scale fuzzy-dedup anchors.
- 01 vision fusion: the fix is the honest reading rule — margin 0.1105
  smaller than vision's own spread 0.2309 is reported as a partial win,
  not a clean one, because seed 2 (0.2844) collapsed below every text-only
  seed while seeds 0-1 beat them by 17-18 points — with the untested
  warmup hypothesis handed forward instead of tuned away post hoc; the
  architecture trade is the fused mask itself (+14,464 parameters, the
  entire cost of sight, against a cross-attention module's per-layer q/k/v
  stack); ownership split across model team (recipe), eval (spread rule
  and text-only control), report (partial-win verdict); ViT (Dosovitskiy
  et al., 2020), PaLM-E (Driess et al., 2023), Flamingo (Alayrac et al.,
  2022), CLIP (Radford et al., 2021) as the contrastive route deliberately
  not taken.
- 02 report: the fix is the pre-declared acceptance bar plus the mechanical
  report (`report.py` prints MET/NOT MET or refuses with CANNOT DETERMINE)
  — verdict NOT MET because the hosted API (0.8329, \$0.00128/question)
  nearly doubles the self-trained pathway (0.4375, \$0 marginal), and the
  per-category read keeps the signal (shape_color 50.1% vs 27.2%, the
  leak-proof category); the trade is that the report cannot soften after
  seeing the numbers, and `total_count` is a task floor (53.0% for the API
  too); ownership split across report (verdict contract), stakeholder
  (declared bar), eval (category taxonomy), model team (reuse claim); Antol
  et al. (2015) for per-category VQA reporting. The audit also corrected a
  number that did not trace to a run: the detour's "hosted API per-category
  floor 0.769" is the recorded 0.969 (shape_color 253/261 in
  `2026-07-31-hosted-api-full.md`).
- 03 real-photo task: the fix is keying each guardrail to the object that
  leaks — image id instead of pixel hash for real photographs (0 overlap
  asserted and re-checked on written records) and VQA v2's own
  `answer_type` as the scoreable filter (yes/no or single-word majority
  answers only; multi-word dropped, never truncated) — priced as the
  refused judge contract and the 32x32 downsample handed to stage 04;
  ownership split across data pipeline, eval, and model team; VQA v2
  (Goyal et al., 2017).
- 04 real-photo fusion: the fix is the per-arm spread read — margin +0.0152
  exceeds vision's own spread 0.0101 while text-only's 0.0707 spread is 7x
  noisier, the variance flipped arms from stage 01 — and the trade is that
  the real margin is a sliver (a third of the synthetic +0.1105), with the
  majority-answer-skew hypothesis stated as unconfirmed and the CPU
  fallback disclosed; ownership split across model team (reuse claim),
  eval (per-arm rule), report (stage-05 verdict); VQA v2 (Goyal et al.,
  2017) for the answer-type distribution the hypothesis leans on.
- 05 real-photo report: the fix is completing the acceptance bar — the
  hosted API on the identical 198-question set (0.4596 vs 0.2374,
  -0.2222) — which confirms buy-not-build on real data, with the
  answer-type-shaped edge (yes/no 0.638, other 0.366, number 0.240)
  naming where a future build could compete; ownership split across report,
  model team, stakeholder, eval; VQA v2 (Goyal et al., 2017).
- 06 warmup stability: the fix is the linear 10%-of-steps LR warmup
  (0 -> 3e-3 over steps 0-185 of 1,860) as the single changed mechanism —
  seed 2 0.2844 -> 0.4962, spread 0.2309 -> 0.0536 (4.3x), mean 0.4375 ->
  0.4970 — and the trade is priced per attempt: one fraction, not swept;
  text-only not re-run; and the final train-loss spread stayed 0.2302,
  proving the fix addressed the optimization path, not seed variance;
  ownership split across model team (recipe and single-mechanism
  discipline), eval (before/after read), report (scope); Goyal et al.
  (2017) and Vaswani et al. (2017) as the warmup anchors.

Detours audited in the same increment: seed-vs-pixels and
the-collision-that-closed-the-gap (the guardrail that passes while the
dataset breaks; the distribution check as the second gate),
the-fused-attention-anatomy (fused prefix vs cross-attention; BLIP-2, Li et
al., 2023 and LLaVA, Liu et al., 2023 as the two production shapes),
where-the-decoder-looks (attention mass is not the explanation — 0.84x mass
on the leak-proof questions; Jain & Wallace 2019 with Wiegreffe & Pinter
2019 as the qualifier), the-economics-per-question (the per-question read
that collapses build-vs-buy onto the accuracy axis), when-the-category-
breaks-down (per-category margins as the pixels-vs-memorization signature),
the-id-based-guardrail and the-real-photo-guardrail (guardrail keys follow
the leak's mechanism), the-flipped-variance and when-the-margin-is-narrow
(per-arm spreads; the noise lives on the control), the-answer-type-shaped-
edge and when-the-api-still-wins (artifact-traceability recomputation;
where the API is weak), and the-collapse-that-warmup-closed and
when-warmup-closed-the-collapse (the eval-spread/train-loss-spread contrast
as the mechanism proof).

### Foundations, infra-absorbed chapters, and remaining missions

**Status: done for foundations 02-optimization, 06-significance, and
07-moe, and for the voice path's modality-imbalance row (ninth and tenth
audit increments, 2026-08-08). The remaining missions named below —
bio-pharma modeling and autonomous driving — were subsequently audited in
full as their own sections (fifteenth and sixteenth audit increments,
2026-08-08).**

**Done for foundations 00-01 (twenty-first audit increment, 2026-08-08).**
The decoder-block and first-training-loop sections now carry the
fix-and-trade and who-owns-the-loop sections the audit contract requires,
each reusing the chapter's own measured numbers:

- 00 attention: the block read as six failure modes with six measured
  trades — score scaling against saturated softmax (sigma 8 to 1, e^24
  vs e^-24 ratio falling to e^6 about 403), the causal mask against
  future leakage, GQA against cache growth (12.0 vs 36.0 MiB, 683 vs
  2,048 concurrency on a 24GB card), RoPE against position-swap
  invariance (wavelength ladder, delta-3 scores identical to machine
  precision), residual + pre-norm against gradients dying across depth,
  SwiGLU against a single projection that cannot both select and
  transform (4,718,592 parameters per block) — with ownership split
  across architecture (block shape), serving (KV-cache ceiling), eval
  (context-extension claims), and training (norm placement); Vaswani et
  al. 2017, Zhang & Sennrich 2019, Shazeer 2020, Su et al. 2021, Dao et
  al. 2022, Ainslie et al. 2023 as the dated anchors.
- 00 attention / rope: the fix is the rotation itself (position
  information that makes attention depend on the gap, not the absolute
  positions), priced by the wavelength ladder and the `rope_theta` knob —
  raising the base to 500k stretches dim 31's wavelength 47,117 to 2.08
  million positions — with the trade that theta is a geometry knob, not a
  capability knob (Su et al. 2021; Peng et al. 2023; Roziere et al. 2023);
  ownership split across architecture (theta), eval (did the model learn
  to use the stretched geometry), and training data (documents that
  exercise long range).
- 00 attention / what-it-costs: the fix is the three-budget distinction —
  parameters fixed, cache linear in context times concurrency, score
  matrix quadratic in context — because conflating the three growth
  curves is how capacity estimates go wrong by an order of magnitude;
  each line's mitigation measured (GQA one-third cache, FlashAttention
  tiling the score matrix out of the budget, weight tying holding the
  embedding at 14.4%); ownership split across architecture (the six
  numbers that fix the total), serving (cache and concurrency ceiling),
  and training (what the arithmetic does not cover: optimizer state,
  activations, fragmentation).
- 01 first training loop: the fix is the three built-in diagnostics — the
  step-0 sanity check (4.3266 vs ln(65) = 4.174: far above is a bug, far
  below is label leakage), the gap read that answers "still learning?"
  from the train/val distance rather than either curve (gap +0.0006 to
  +0.2630), and the data-not-model lesson (0.3M tokens supplied vs ~215M
  compute-optimal for 10.75M parameters; Hoffmann et al. 2022) —
  ownership split across training engineer (health checks), data team
  (generalization ceiling), and eval (overfitting read with its boundary).
- 01 first training loop / the-curve-that-takes-34-seconds: the fix is
  reading the curve as a pair — descent shape as health check, gap as the
  generalization signal — because the val number still improves to the
  end while the gap widens monotonically; ownership split across training
  engineer (health shape), eval (gap read and handoff), data team (the
  corpus-size lever that closes it).

**Done for foundations 03-05 (twenty-second audit increment, 2026-08-08).**
Backpropagation, distributed training, and the significance chapter now
carry the fix-and-trade and who-owns-the-loop sections the audit contract
requires, each reusing the chapter's own measured numbers and citing dated
sources:

- 03 backpropagation: the accumulation-vs-assignment fix priced by the
  diamond expression (flipping `+=` to `=` moves only the reused `a`, from
  +0.3577 to -0.2504, while single-consumer `b` 0.3505 and `c` 0.5008 stay
  correct — a dropped contribution corrupts tied embeddings silently) and
  the two-check verification protocol (engine-vs-analytical 0.0,
  engine-vs-torch 1.11e-16, float64's floor); Linnainmaa 1970 and
  Rumelhart, Hinton, and Williams 1986 anchor the mechanism; ownership
  split across framework (the `+=` invariant), training engineer (the
  two-reference protocol), and platform (batching, devices, fusion as the
  unclaimed layers).
- 04 distributed training: the assertion protocol that catches silent rank
  drift (pre-reduce delta 0.000119 beside the asserted 0.0 divergence — a
  desync never crashes) and the ZeRO trade (optimizer state 2.62 to 1.05 MB
  per rank, 2.5x not 4x because 5 tensors over 4 ranks cannot divide
  evenly — production shards by element count; memory down, communication
  up); Rajbhandari et al. 2020 (ZeRO), Shoeybi et al. 2019 (Megatron TP),
  Narayanan et al. 2021 (Megatron pipeline); ownership split across
  training engineer (assertion protocol), framework (sharding arithmetic),
  and platform (the unmeasured bandwidth half).
- 04 gpu-cluster-concepts and when-the-topology-costs: the conflation fix —
  coordination, not bandwidth, is what grows (4 MB fixed payload, per-call
  all-reduce 1.8181 to 3.5970 to 8.3138 ms, x1.98 then x2.31; growth x4.57
  at world 8 read from the record) — so parallelism placement follows the
  per-step collective count, not a single number; Thakur, Rabenseifner, and
  Gropp 2005 (bandwidth-optimal ring), Shoeybi et al. 2019, Narayanan et
  al. 2021; ownership split across platform (wiring), benchmark owner (the
  latency-vs-bandwidth label), and training engineer (bucketing).
- 04 networking and when-the-ring-beats-the-star: the ring-vs-star fix —
  ring halves bytes per rank at every cell (star exactly 2x ring; world 8
  32 MB: 1.0304s vs 0.5080s, time ratio 0.49x at 32 MB and 0.24x at 8 MB)
  and the deadlock fix (send-then-receive blocking past the OS pipe buffer;
  background-thread drain), trading liveness for per-rank thread overhead;
  the byte ratio is the scaling law, with world-2 cells noisy because
  latency dominates small payloads; Thakur et al. 2005; ownership split
  across framework (collective implementation), training engineer (bucket
  size decides which regime), and benchmark owner (multi-payload sweep).
- 04 orchestration and when-the-scheduler-chooses: the measurement-protocol
  fix that removed the cold-start confound (first run 0.0389s vs 0.0202s —
  warmup order, not policy; fixed to 0.0182s vs 0.0187s) and the
  reallocation read — priority cuts high-priority wait ~6x (0.0074 to
  0.0012s) at the cost of low-priority wait (0.0074 to 0.0094s) with
  makespan fixed; Yoo, Jette, and Grondona 2003 (Slurm); ownership split
  across platform (policy and the wait-distribution metric), job owners
  (priority labels), and benchmark owner (warmup and alternating order).
- 04 storage and when-a-node-joins: the placement-rule fix — modulo remaps
  0.802 (four times the 0.200 ideal) and moves 105 MB versus consistent
  hashing's 0.180 and 24 MB on a real 4-to-5-node disk remap, because the
  modulus change rehashes every key; consistent hashing trades modulo's
  trivial uniformity for the virtual-node load-balance knob, with
  replication and partial-failure semantics outside the run; Karger et al.
  1997, DeCandia et al. 2007 (Dynamo); ownership split across storage
  (placement rule), checkpoint-format owner (shard assignment), and
  training engineer (world-size changes between runs).
- 04 when-the-ranks-agree: the two-fix table — the assertion protocol
  (0.000119 proves ranks differ, asserted 0.0 proves the merge) and the
  ZeRO-1 trade (2.62 to 1.05 MB with divergence still 0.0; the 2.5x-vs-4x
  gap is the ownership rule, not the world size); Rajbhandari et al. 2020;
  ownership split across training engineer (the printed pair), framework
  (sharding arithmetic), and platform (the unmeasured communication cost).
- 05 is-the-difference-real: the multi-seed harness with a returnable
  "not detectable" verdict — the crossover is measured (n=8 interval
  -0.0214 ± 0.0271 spans zero; n=16 -0.0273 ± 0.0209 does not, torch/Welch
  agreeing at p=0.0001), and the run honestly labels that the mixtures were
  tuned to put the crossover on screen, so seed count is a property of the
  effect; Hoffmann et al. 2022 (Chinchilla), Sainz et al. 2023
  (contamination); ownership split across research (mixture and seed
  protocol), eval (verdict contract), and training (transfer assumption).
- 05 the-two-confounds: the two fixes are the two-size ladder (trust a
  ranking only where it is stable across two sizes — a flip says the proxy
  does not transfer, not which size is right; doubled run budget) and the
  comparable-teacher control with a contamination-safe eval set (synthetic
  data earns only what verification supports: works where verification is
  cheaper than generation, fails where the filter is the generator marking
  its own work); Hoffmann et al. 2022, Gunasekar et al. 2023, Sainz et al.
  2023; ownership split across research (the ladder), eval (contamination
  boundary), and data (teacher choice).

**Done for the corpus stage and the pretraining sub-group (twenty-third
audit increment, 2026-08-08).** The `00-corpus/` parent and every
`02-pretrain/` chapter now carry the fix-and-trade and who-owns-the-loop
sections the audit contract requires, each reusing the chapter's own
measured numbers and citing dated sources:

- 00-corpus: the funnel as case-finding (20,000 in, 4,592 out, 23% —
  language ID is the single biggest filter, removing 10,862 of 20,000) and
  the cross-implementation audit that catches the naive pipeline being 40%
  too permissive (9,184 kept at 23.0% vs datatrove's 5,513 at 13.8%, the
  gap named as repetition the funnel is blind to); the trade is speed
  against structural awareness (regex ~2 ms/doc vs trafilatura 25 ms/doc,
  85% of datatrove's runtime); ownership split across data (funnel
  contract, per-gate drop reasons), platform (production recipe and the
  distributed dedup), training engineer (the length shape, median 322 vs
  mean 705), and eval (contamination boundary); Rae et al. 2021, Raffel et
  al. 2019, Penedo et al. 2024, Lee et al. 2022 (dedup), Sainz et al. 2023
  (contamination).
- 02-pretrain parent: the wrong-objective read (a falling loss is
  next-token agreement, not truth — 3.0689 nats converts to 4.65% on the
  right token, one in 21.5), the budget arithmetic (C about 6ND, 34 tokens
  per parameter vs Chinchilla's ~20, deliberately over-trained because
  serving cost tracks parameters), and the step-0 floor that catches silent
  wiring bugs (ln(16,512) = 9.712; measured 9.8697; far below means the
  model sees the answer); Hoffmann et al. 2022; ownership split across
  training engineer, data, serving (the KV-cache tax), and eval.
- 02-pretrain attention-variants: the linear-in-context cache tax priced
  per variant (MHA 36,864 bytes/token, GQA 12,288, MQA 3,072, MLA 0.67x of
  this repo's MHA against the paper's 93% because ratios are
  baseline-relative), and the K3 four-condition test that bundles quality,
  training/prefill cost, cache, and decode compute; Vaswani et al. 2017,
  Ainslie et al. 2023, Shazeer 2019, DeepSeek-V2 2024; ownership split
  across architecture (head count baked at training), serving (the
  per-request collection), and eval (the unmeasured quality drop).
- 02-pretrain the-gate-that-beats-relu: the dead-neuron tax (ReLU 50.1%
  near-zero units on 200k draws — a dead unit's gradient is zero, so half
  the block is inert) fixed by the multiplicative SwiGLU form (zero-mean
  -0.001, no dead zone, a conditioning property for the following RMSNorm),
  traded at more than twice the parameters at the same width; Shazeer 2020;
  ownership split across architecture (block form), training (norm
  conditioning), and eval (the random-input boundary).
- 02-pretrain upcycling and does-it-pay-off: the all-or-nothing assumption
  fixed by the surgery plus its verify check (four identical experts make
  top-k routing irrelevant at step 0, so the converted model must start at
  the parent's 3.0498, not the 9.7118 floor — a load at 4.2 is a failed
  conversion), priced at 2.93x storage and 1.64x compute with 1.93x
  measured wall-clock (the Python-loop dispatch gap, a kernel cost); the
  continuation pair (both arms rise to 3.1445 at 53M, crossover at 32.8M,
  -0.0088 at 200M monotone) and the equal-wall-clock blank (dense would
  have seen 391M tokens in the MoE arm's 1,645.9s — unrun, so a blank, not
  a tie); ownership split across training engineer, research (budget
  declaration), platform (kernel dispatch), and eval (one seed per arm
  bounds nothing — the shape carries the result).
- 02-pretrain latent-reasoning: the tokenization tax on reasoning (a
  768-number state collapsed to one of 16,512 choices) fixed by the
  continuous-thought loop and the curriculum that supervises thoughts
  through staged replacement; measured collapse is the failure mode — cot
  0.9993 vs direct 0.502, latent 0.502 with per-stage accuracy hitting 1.0
  at n_latent=3 and collapsing at n_latent=4; the trade is n+1 forward
  passes and KV-cache invalidation on slot overwrite; Hao et al. 2024;
  ownership split across research, training engineer (curriculum), and
  serving (token-vs-pass economics).
- 02-pretrain architecture-ablations and the-rung-that-flipped: the
  underdetermined comparison — equal-parameter, equal-FLOP, and
  equal-wall-clock definitions routinely disagree, so `core/ablate.py`
  refuses to write a result file without a budget definition; the noise
  floor (six identical runs spanning 0.0018 from GPU nondeterminism) makes
  claims under ~0.002 noise, and the nine feed-forward runs support two
  opposite headlines (MoE wins 0.0901 under equal-active, ties 0.0001
  sign-flipping under equal-total, and equal-wall-clock is a blank because
  the dense-at-391M arm was never run); Zhang & Sennrich 2019, Su et al.
  2021, Shazeer 2020, Ainslie et al. 2023, Fedus et al. 2022, Hoffmann et
  al. 2022; ownership split across research (budget), training (seeds and
  batches), eval (two-size stability), and platform (hardware
  attribution).
- 02-pretrain when-the-curve-goes-wrong: the unattributed curve (best
  3.0689 at step 21,000, rising to 3.0984 at 22,500; three candidate
  owners, one run cannot separate them) fixed by the pair-reading table and
  the injected-failure telemetry (gradient norm departs two steps before
  the loss; bf16-master flatlines at 2.418 vs fp32-master 2.358 with the
  gradient norm alive at 0.050; overflow goes non-finite at step 3), the
  mixed-precision contract (bf16 activations, fp32 master weights and
  accumulation, explicit non-finite checks), and the continued-pretraining
  four rules; Micikevicius et al. 2018, Gururangan et al. 2020, Peng et al.
  2023; ownership split across data, training, eval, and ML-infra.
- 02-pretrain throughput: the unreadable tokens-per-second fixed by MFU
  (4.5% to 65.9% across a 14.69x spread of the identical model) with five
  flags measured one at a time (flash attention 2.94x, compile 1.72x, fused
  AdamW 1.03x, activation checkpointing -17% for 2.5x memory) and the
  profiler attribution proving the matmuls did not move (aten::mm 275.8 to
  277.5ms while 341ms of elementwise work disappeared); the silent-OOM trap
  (fp32 rung needed 27.7 GB on a 24.5 GB card and WSL2 paged instead of
  failing — bf16 is 1.28x, not 2.82x, so peak-memory must be read before
  throughput); Dao et al. 2022; ownership split across training engineer,
  platform, benchmark owner, and eval.
- 02-pretrain verifying-the-run: the five-hour-job-that-merely-runs fixed
  by the first-minute checks — the step-0 floor (9.8697 vs ln(16,512) =
  9.712; far below is label leakage), the gradient-accumulation division
  (omit it and gradient x8 is LR x8, silent, no log line), and MFU at
  minute one (85.5k tokens/s at 33.3% projected 9.8 hours; compile moved it
  to 165.6k and 64.5%, a 1.76x speedup and a 4.98-hour run) — plus the
  reported rising tail (3.0689 to 3.0984, saved final checkpoint, not best)
  and the fluency-versus-grounding boundary (4.65% probability on the right
  token is real learning and nowhere near knowing the sentence); Hoffmann
  et al. 2022; ownership split across training engineer, eval, data, and
  platform.

**Done for the SFT sub-group (twenty-fourth audit increment, 2026-08-08).**
The three pending `03-sft/` chapters now carry the fix-and-trade and
who-owns-the-loop sections, reusing the chapter's own measured numbers and
dated citations, and the six chapters that carried the ownership section
under a non-contract heading (`## Who owns it` / `## Who owns the contract`)
were normalized to `## Who owns the loop` so the contract's check is
uniform:

- 03-sft parent: the base model's indifference to conversation fixed by the
  loss mask (`-100` is `cross_entropy`'s default `ignore_index`, so the
  loss is computed only on assistant tokens; the closing `<|im_end|>` is
  trained on deliberately so the model learns to stop) and the
  one-convention template rule (ChatML vs Alpaca markers are arbitrary; a
  serve-time mismatch degrades toward base behavior); the cost is measured
  — 92.5s over 9,500 conversations, val 3.1829 to 2.7828, 19.6% padding,
  217 conversations discarded, and the step-0 baseline is its own curve,
  not pretraining's; Zhou et al. 2023 (LIMA); ownership split across data
  (the four pre-data failure modes), training engineer (mask and template),
  eval (honest baseline), and serving (template version at inference).
- 03-sft what-it-costs: the cost invisible in the loss curve — packing's
  attention leak (late tokens in conversation B attend to A; blast radius
  bounded because the loss depends only on labels, never attention),
  the thirtyfold learning-rate drop (6e-4 applied to a converged model
  re-randomizes it; 2e-5 protects the prior, and many epochs at the old
  rate is how catastrophic forgetting happens), and the four things better
  data cannot fix (no new knowledge, no ground truth, no preference signal,
  no capacity — LIMA's doubling-the-set non-improvement vs the multi-turn
  addition raising "excellent" from 45.2% to 76.1% anchors curation over
  volume); Zhou et al. 2023; ownership split across training engineer,
  data, eval (the forgetting probe against the base checkpoint), and
  platform (the four limits' escalation boundary).
- 03-sft what-model-size-changes: the single-point claim fixed by the size
  axis — the 5M run (pretrained-base SFT 9.5188 to 8.6496 vs random-init
  9.7475 to 8.8015: the base prior helps even at 5M, and neither arm lands
  the format, producing word fragments) read against the recorded 88M point
  and dated external results (LIMA 65B 2023; token-scaled vs fact-scaled
  SFT arXiv:2509.16596 2025; Chu et al. ICML 2025 "SFT Memorizes, RL
  Generalizes"); ownership split across research (which points are measured
  vs attributed), training engineer (the controlled comparison), and eval
  (the format-vs-content mechanism read).
- 03-sft beyond-demonstrations: the two broken arrangements (nobody wrote
  the answer; moving every weight is too expensive) fixed by LoRA (48x
  fewer parameters, 0.56% of the model, rank constrains update direction),
  reward models (sigma sees only the difference, so a reward is meaningless
  beside its comparison and annotator agreement sliced by exploitable
  failure modes is the check), DPO (step-0 loss exactly log 2 = 0.693, the
  reference-model check), and task-vector merging (three full checkpoints,
  shared-base precondition); none run here, so the figures are worked
  arithmetic on real shapes; Hu et al. 2021, Dettmers et al. 2023, Rafailov
  et al. 2023, Meng et al. 2024, Ilharco et al. 2022; ownership split
  across training engineer, data, eval (the offline boundary), and research
  (the no-run boundary).

**Done for the serve sub-group (twenty-fifth audit increment, 2026-08-08).**
The six pending `05-serve/` chapters now carry the fix-and-trade and
who-owns-the-loop sections, reusing each chapter's own measured numbers (no
new runs):

- graph-execution: the launch-bound step (the card busy 15% of the time,
  513 launches per step, 6.87x host-to-device) found with a profile rather
  than a benchmark; fix is CUDA-graph capture, trading arithmetic for
  launches (device time up 2.12x to 2.807 ms/step, wall-clock down 3x,
  measured 2.92x/3.05x/3.06x, replay 15x more stable) with `torch.compile`
  getting 2.47x blind and the remaining gap available only to code that can
  promise capture safety; NVIDIA "CUDA Graphs" 2019, PyTorch
  `torch.cuda.CUDAGraph` and `torch.compile` docs; ownership split across
  serving-performance (profile verdict), inference-engine (identity-check
  guardrail), evaluation (median-vs-spread statistic), and model (the
  workload-scoped multiplier).
- quantization: the smaller-checkpoint-slows-decoding failure (2.79x fewer
  bytes, 0.76x eager) found with the correctness gate (greedy exact match
  1/64 while cosine 0.99975 / KL 0.0027 — argmax flips on close top-2,
  7.72% vs 6.44%) and the profile (device time up 35%, dequant materialises
  fp32 every call); fix is the workload verdict — quantize only when decode
  is bandwidth-bound and benchmark the runtime, never the file size —
  trading memory for runtime work (3.98x layer bytes, torchao fused int8
  slower still at 0.68x, unmeasured dispatch overhead stated as
  hypothesis); Dettmers et al. 2022, Frantar et al. 2023, Xiao et al.
  2023; ownership split across serving (axis and kernel-support decision),
  evaluation (distributional gate and outlier slices), model (calibration
  corpus), and kernel-infrastructure (fused path).
- speculative-decoding: the draft-that-costs-more-than-it-saves failure
  (1.58x at 37.9% acceptance vs 0.94x at 15.9%, same architecture, 600 vs
  40 training steps) found by measuring acceptance per request slice; fix
  is the one-pass verification contract — correctness by construction
  (byte-identical output asserted over 200 tokens), the trade being draft
  and verification cost paid every round and a workload-specific crossover,
  with only the greedy variant measured (CPU wall-clock, no GPU) and the
  stochastic algorithm cited externally (Leviathan, Kalman & Matias 2023;
  Chen et al. 2023); ownership split across serving (pairing and k per
  slice), evaluation (acceptance measurement), model (draft quality), and
  product (the SLO speculation must not threaten).
- observability: the mean-hides-the-tail failure (p50 18.45ms and mean
  18.72ms hide the 29.94ms max, 1.6x the mean) found by collecting the
  distribution — one perf-counter sample per step after 5 warmup steps,
  read as p50/p95/histogram from the same 200 samples; fix is the reporting
  contract (p50 and p95, never a lone mean), the trade being that
  percentiles need enough samples to stabilise and that a counter and a
  histogram answer different questions, with the CPU-only tail causes (GC,
  OS jitter) explicitly not the production ones (data-loader stalls, NCCL
  stragglers, checkpoint writes); Dean and Barroso, "The Tail at Scale,"
  CACM 2013; ownership split across observability (distribution contract),
  training-infrastructure (tail escalation), evaluation (budget decision),
  and model (histogram-shape diagnostics).
- observability when-the-tail-waits: the mean-based budget failure (a
  25ms budget silently fails the 20% of steps above it) found by reading
  the recorded distribution; fix is budgeting from p95 (21.14ms, above the
  mean by 13% and below the max by 42%) or p99, trading strictness for
  coverage, with the evidence boundary explicit (recorded 200-step artifact,
  no GPU or multi-tenant extension); ownership split across observability
  (histogram contract), serving (the timeout and percentile choice),
  evaluation (budget decision), and model (max-vs-mean as the
  hidden-tail signal).
- paging-the-cache: the reservation failure (production systems reported
  60-80% of KV cache wasted before PagedAttention; a 20-token sequence
  sized for 1,024 wastes 1,004 slots) found with a per-sequence allocation
  view — two kinds of waste that respond to different fixes; fix is the
  page table (fixed-size blocks from a shared free list plus a per-sequence
  block table, 16 tokens here), trading internal fragmentation against
  indirection overhead (12 vs 44 vs 0 slots at 16/64/4-token blocks) while
  eliminating external fragmentation and making copy-on-write and prefix
  caching expressible; measured boundary explicit — the gather is unfused,
  so no throughput number transfers; Kwon et al., SOSP 2023; ownership
  split across serving-infrastructure (allocator and block size), capacity
  (KV budget and admission), kernel (the fused path), and observability
  (sharing gains as a property of the request mix).

**Done for the agent sub-group (twenty-sixth audit increment, 2026-08-08).**
The four pending `06-agent/` chapters now carry the fix-and-trade and
who-owns-the-loop sections (when-the-tool-errors already carried the
who-owns half, so only the fix-and-trade was added), reusing each chapter's
own measured numbers (no new runs):

- what-stops-it: the containment failure — every capability is also a way
  to do damage, and grounding makes the agent honest, not safe (the demo
  run proves the `cat /etc/passwd` gap with 71 real lines); fix is the
  containment stack — jail with reject-absolute-before-joining ordering,
  allowlist that depends on never passing `shell=True`, three-tier
  permission ladder, default-deny `confirm` (absence of a human is not
  consent) — trading coarse tool-level tiers and lost shell expressiveness
  for a fail-closed boundary, with the destination ladder keeping the
  confirmation rate proportional to stake; adversarial half benchmarked,
  not assumed (AgentDojo, Debenedetti et al. Jun 2024; Anthropic
  `tool_result` block, OpenAI `"role": "tool"` message); ownership split
  across harness (stack and fail-closed rule), product-security (permission
  policy), platform (process isolation, namespace, dropped privileges), and
  evaluation (score under harness disclosure).
- what-fits-in-context: the transcript-overflow failure (delete the wrong
  thing and the agent forgets the task; delete nothing and the loop dies at
  step twelve); fix is a named swappable compaction policy — collapse
  superseded reads before dropping turns, floor of 3 messages — measured
  (1,784 tokens reclaimed from one stale read, zero turns dropped; seven
  compactions then stop at 3 messages, staying 50 vs 30 tokens over budget
  rather than erasing evidence); trade is lossless-before-destructive
  ordering and the floor that stops the policy breaking the loop, with
  MemGPT paging (Packer et al. 2023) the heavier alternative and the
  chars/4 estimator risk on code stated; ownership split across harness
  (policy and floor), tool-design (just-in-time choice that makes
  per-observation compaction workable), evaluation (verified in isolation
  only — the real run never crossed the token budget), and model
  (estimator risk).
- would-a-second-agent-help: the oversold-multiplier failure (error
  compounds along a chain, cost multiplies while quality does not,
  debuggability collapses); fix is the orchestration contract — parent
  owns scope/permissions/budget/stop/result shape, child owns how it gets
  there, structured returns over prose, parallel-safety rule enforced by
  the scheduler — with the fair test holding total token cost equal and the
  measured 7.6x handoff tax (737 vs 97 tokens) while wall-clock fell
  four-to-three batches: parallelism and cost are different axes; dated
  origins (Du et al. May 2023, Wu et al. Aug 2023, LangChain Jan 2024);
  evidence boundary explicit — no topology success claim measured; ownership
  split across framework (contract and scheduler), evaluation (matched-spend
  bar), platform (production mapping), and model (handoff loss).
- when-the-tool-errors: the blind-retry failure (0/7 classes resolve; the
  already-executed trap — `slow_write.py` times out yet leaves `marker.txt`
  with content `done`, and two of seven failures are returned, not raised);
  fix is the recovery families (inspect, re-scope, make it safe to redo —
  7/7 resolved for real), the trade being that recovery has to be in the
  imitation data, a pipeline decision whose measured scale is external
  (PALADIN arXiv:2509.25238 Sep 2025: 17.5% to 78.7% tool-success; Chen et
  al., Self-Debug, ICLR 2024); ownership split across trace-construction
  (error injection), eval (per-class recovery rate), harness (idempotency
  surface), and model (data-composition consequence).

**Done for the eval sub-group (twenty-seventh audit increment, 2026-08-08).**
The five pending `07-eval/` chapters now carry the fix-and-trade and
who-owns-the-loop sections, reusing each chapter's own measured numbers and
dated citations (no new runs):

- metric-gaming: the structural proxy failure (an optimizer finds the
  peeled-away directions once the genuinely useful lever saturates — the
  measured sign flip, +0.807 then -0.998 to -1.000, with the proxy-only
  optimizer at 371.85 while the true objective falls to -381.00 and the
  control stops at 70.71); fix is treating gameability as part of proxy
  selection and auditing exploitable dimensions before optimization finds
  them, the trade being that the gold-signal defense costs exactly what the
  proxy was built to avoid (held-out human review, independent judge,
  occasional gold metric); Singhal et al. arXiv:2310.03716 2023, Goodhart
  1975; ownership split across evaluation (proxy selection and gameability
  check), product (true objective and gold signal), modeling (optimization
  pressure), and platform (gold-metric sampling cadence).
- red-teaming: the fixed-test-set failure (a system passes every authored
  case while a nearby variant breaks it — measured flip rate 0.000 at every
  budget up to 1000 with case-flip-only operators vs 100% by budget 10 with
  the full operator set: budget cannot substitute for perturbation
  coverage); fix is the manual-plus-automated pair and the bounded-claim
  discipline ("we tried N variants and found none" is a dated claim about a
  search process, never a robustness proof); Perez et al. Feb 2022 / EMNLP
  2022, Ganguli et al. Aug 2022, Debenedetti et al. Jun 2024; ownership
  split across safety-evaluation (search and operator coverage), data (case
  library and dating), model (response to a discovered failure), and
  release (escalation chain to a stopped deployment).
- who-decides-to-ship: the score-versus-decision gap (outcome-only metrics
  record a forbidden-action success as success; a guardrail you cannot
  compute is a wish; measurement after the fact is not enforcement); fix is
  the five-condition gate, enforcement at the subsystem that can still say
  no, and the provenance record, the trade being blast-radius discipline
  and converting arguments into measurements; evidence boundary explicit —
  none of it is measured here, with eval gates and red-teaming as the
  run-backed pieces; ownership split across release (gate and five
  conditions), permission-policy (taxonomy row five), product (guardrail
  contract), and platform-audit (provenance and enforcement points).
- whose-harness: the undisclosed-harness failure (a score is a function of
  seven terms, published comparisons disclose the first — measured
  consequence: ARC-AGI-3 13.3% to 38.3% with the model unchanged, one
  setting a defect, the other a declared policy); fix is the always-do five
  plus the declared-choice column enforced by `REQUIRED_HARNESS_FIELDS`
  raising, the trade being that a generic harness measures the model and a
  tuned harness measures the product, neither being "the score", with
  lm-eval-harness for static comparability (lambada_openai 20.5%, 138.3
  perplexity) and an own harness for trajectories; ownership split across
  evaluation (harness contract), model (deployment-contract match),
  benchmarking-platform (adapter and version pinning), and product (which
  measurement a release needs).
- why-believe-the-number: the false-number failure in three forms —
  contamination (SWE-bench Verified's public fix PRs; SWE-bench Pro /
  Terminal-Bench 2.0 as the documented response), judge bias (position,
  verbosity, self-preference; Zheng et al. 2023; AlpacaEval 2.0 length
  control), and variance (300 samples at 50% = ±5.7 points; seed and
  environment spread on top); fix is the reporting contract (date every
  number, both uncertainties, judge validated against a gold set), the
  trade being partial defenses whose missing parts are the disclosures;
  Jiménez et al. 2024; ownership split across evaluation (disclosure
  contract), data (benchmark selection and contamination risk),
  product-quality (the gold set), and model (judge choice as a structural
  countermeasure).

The language-model system now satisfies the contract end to end: stages
00-07, the serve/agent/eval sub-groups, and the vision path all carry the
failure-mode, fix-and-trade, and who-owns-the-loop sections with measured
or attributed-and-dated evidence.

**Still pending:** a gap re-check of the remaining topics against the
contract (personalized discovery, quantitative research, agentic platform,
game AI, multimodal voice/video, bio-pharma, autonomous driving are done as
of the increments above; the check re-reads them because earlier user
feedback flagged personalized discovery chapters as shallow). A fresh scan
on 2026-08-08 measured the current coverage per topic:

- 02-personalized-discovery: 265 chapters, 52-53 carry fix-and-trade and
  who-owns sections — the largest gap, matching the user's shallow-content
  flag; re-read stage ranges against the 265-chapter reality.
- 03-quantitative-research: 19 chapters, 12 carry both — 7 missing.
- 05-game-ai: 22 chapters, 21 carry both — 1 missing (no fix-and-trade).
- 07-multimodal-generation: 46 chapters, 25 carry both — 21 missing, all
  in the video path (voice path carries them).
- 08-bio-pharma-modeling: 22 chapters, 21 carry both — 1 missing.
- 09-autonomous-driving: 8 chapters, 7 carry both — 1 missing.

The re-check works the topics in that order, one increment per topic, using
the same fix-and-trade / who-owns contract as the language-model topic.

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

**Structural re-check 2026-08-08 (thirtieth audit increment):** a fresh
scan found the parents of 02, 06, and 07 still missing the fix-and-trade
section and every one of their five detours still missing who-owns,
even though the summary above claimed the row done. Closed now, each
section reusing the chapter's own measured numbers: 02 optimization
parent's fix is the larger effective step on the shallow axis — at A = 10
plain SGD stops flipping signs entirely (zero flips) and still needs 343
steps, so the crawl, not the zigzag, sets the pace, and momentum (138)
and Adam (82) win by moving faster there, with the A = 1000 divergence
of SGD and momentum pricing the fixed-step-size side of the trade; its
two detours now name owners (optimizer team for the update rule and mu
knob, infra for conditioning and budget, research/eval or data/capacity
for the surface-floor class where all four rules stall at the same
0.0100). 06 significance parent's fix is the ship-on-the-interval rule —
the same true +0.06 effect shows a larger gap at n=25 (0.2000) that the
(−0.0400, 0.4400) interval does not support, versus n=300's 0.1333 with
(0.0600, 0.2067); its two detours now name owners (measurement team for
the report and pre-registration, statistics team for the correction
choice at 0.59-to-0.22 false positives and 6/500-to-25/500 power cost,
product owner for what a false win costs). 07 moe parent's fix is the
balancing term — auxiliary loss at alpha = 1e-2, capacity factor, and
Quantile Balancing — traded against routing quality and per-step
histogram cost, with accuracy fixed at 1.000 in every cell; its detour
now names owners (architecture for the balancing objective, serving for
the capacity factor and drop, evaluation for the count-based utilization
check). Every one of the nine chapters now carries both sections; the
scan is clean for the whole foundations row.

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

**Status: done (fourteenth audit increment, 2026-08-08; interactive wiring
2026-08-09 for stages 03, 04, 06).**

On 2026-08-09 stages 03, 04, and 06 each received a ProcessDiagram wired
to the recorded runs: fixing-collapse (baseline greedy 0.062-0.078 vs
small-group 0.024-0.050 and entropy-bonus 0.078, entropy rising
1.3-1.7 nats), MiniGrid cold start (500/500 heuristic vs 2/500 random,
80/80 degenerate steps on all 3 seeds), and tool-use decision
(seed 0 matches the oracle at all 5 levels, seeds 1-2 always-answer,
3-seed mean 0.7953).

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

**Structural re-check 2026-08-08 (twenty-ninth audit increment):** stages
00 and 02-06 now carry the same `## The fix and its trade` and `## Who owns
this loop` sections stage 01 carried, each before its evidence boundary,
reusing each stage's own measured numbers (the 1-of-150 rejection against
mission 05's 116 collisions and the near-35,600 effective space; the 37.2%
baseline beat with the 6.7-22% exact-match caveat and the +0.0008
wrong-token reconstruction gap; the margin 0.0430 vs spread 0.0078 verdict
paired with 8.4-8.6% of the 1800s ceiling; the 4.3x cost for 2x frames and
the 2.7-to-24.6-point exact-match spread; the 74% two-object MSE jump with
exact-match collapsing to 0.67-28.67%; the 16x2 corner at 0.1375-0.1456
MSE with exact-match 0.00-0.67% and the frame-count binding assert). With
this, every chapter in the video path satisfies the audit contract at the
parent and detour level.

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

**Structural re-check 2026-08-08 (twenty-eighth audit increment):** the
six parents (stages 00-05) now carry the same `## The fix and its trade`
and `## Who owns the loop` sections the detours carried, each before its
evidence boundary, reusing the stage's own measured numbers (the 4% naive
join mismatch and the MSFT \$1.75B restatement; the 95-of-300 matching null
searches and the all-200-replicate noise beat at 1,024 candidates; the
7-to-47 cap re-breaches and the -0.68-to-1.20 paper Sharpe range; the
0.7393/0.9722/0.9722 paths and the 14-trial deflation to 0.3145; the USD
25bn liquidity peak against the USD 125bn cost breakeven and the USD 31.6B
net-dollar peak; the 18 named missing inputs behind CANNOT DETERMINE).
With this, every chapter in the quant range satisfies the audit contract
at the parent and detour level.

### Agentic platform — 00-06

**Status: done (twelfth audit increment, 2026-08-08; interactive wiring
2026-08-09 for stages 01, 04, 05, 06, 07).**

On 2026-08-09 stages 01, 04, 05, 06, and 07 each received a ProcessDiagram
wired to the recorded runs: no-harness (18/18 vs 4/18 blind; sonnet
\$1.3744 vs \$0.5369 per resolved), how-it-fails (12/18 target_still_failing,
11 never applying; 0/18 tampered in both arms), the report (1 PARTIAL /
6 MET, opus margin inside its own spread at N=2), closing-the-loop
(0/12 to 2/12 after one retry, fully bimodal), and the frontier index
(4/18 produced, 14/18 rejected at the gate, 18/18 delivered).

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
