---
status: verified
level: applied
base: scratch
label: Search evaluation
verified: 2026-08-06
---

# What search success means, and what each metric hides

**Question:** search evaluation answers "did the ranking work" with a
metric — and the metric choice changes what gets optimized. This stage
computes NDCG@k and MRR and shows their blind spots.

**Before this:** [stage 12 — search ranking](../12-search-ranking/) for the
ranker, and [mission 01's evaluation](../../../01-language-model/07-eval/)
for why a metric must be disclosed.

## The metrics, executed

The run ([record](runs/2026-08-06-search-eval.md)) computes both metrics
on four rankings:

| ranking | NDCG@5 | MRR |
|---|---:|---:|
| A: one good hit early | 1.0000 | 1.0000 |
| B: good spread | 0.8140 | 1.0000 |
| C: good at top | 1.0000 | 1.0000 |
| D: reversed | 0.2750 | 0.2500 |

<!-- interactive: SearchEvaluation -->

## The mechanisms, named

1. **NDCG** — graded relevance, discounted by position, normalized against
   the ideal ordering. Rewards putting relevant items high and is
   sensitive to grade.
2. **MRR** — the reciprocal rank of the first relevant hit. Rewards one
   early hit and ignores everything after it.

## The blind spots, executed

B's "good spread" (grades 1, 2, 2, 1) scores NDCG 0.814 but MRR 1.0000 —
identical to A's single good hit. MRR cannot tell "one good hit" from "a
consistently decent ranking." And C's NDCG 1.0000 hides that the third
position, grade 0, is a miss the ideal would have avoided — NDCG is
insensitive to what sits below the top-weighted region when the top is
correct. The metrics agree on the extremes (D is clearly bad) and disagree
where the decision actually is, which is why evaluation reports several
metrics together.

## How you find it: the metric-divergence audit, executed

Reporting several metrics only helps if someone checks whether the
leaderboards agree. The run ([record](runs/2026-08-07-search-evaluation-audit.md))
emits the graded rankings plus three audit rankings, and the audit
builds both leaderboards with competition-style ranks:

| ranking | NDCG | NDCG rank | MRR | MRR rank | gap |
|---|---:|---:|---:|---:|---:|
| A: one good hit early | 1.0000 | 1 | 1.0000 | 1 | 0 |
| C: good at top | 1.0000 | 1 | 1.0000 | 1 | 0 |
| G: ndcg gamer | 0.8750 | 3 | 1.0000 | 1 | 2 |
| B: good spread | 0.8140 | 4 | 1.0000 | 1 | 3 |
| F: first-hit gamer | 0.7519 | 5 | 1.0000 | 1 | 4 |
| H: spread, early miss | 0.5831 | 6 | 0.5000 | 6 | 0 |
| D: reversed | 0.2750 | 7 | 0.2500 | 7 | 0 |

The verdict is METRIC DIVERGENCE: MRR ties five rankings as joint best
that NDCG separates across five ranks, and the first-hit gamer F (one
mediocre hit first) is MRR-perfect and NDCG-fifth. Järvelin and
Kekäläinen ("Cumulated gain-based evaluation of IR techniques", ACM
TOIS 20(4), 2002) motivate graded gain for exactly this reason;
Joachims ("Optimizing Search Engines Using Clickthrough Data", KDD
2002) is why click-based online variants of the same games compound
through position bias.

## The fix and its trade

The fix is a declared metric suite — graded labels, per-position NDCG@k
curves, and a rank-gap audit that names which metric each ranking
exploits. The executed audit prices the failure the fix removes: MRR ties
five rankings as joint best that NDCG separates across five ranks, and
the first-hit gamer F is MRR-perfect (1.0000) while NDCG-fifth (0.7519).
The blind spots are structural: B's good spread scores MRR 1.0000 —
identical to A's single good hit — and C's NDCG 1.0000 hides a grade-0
miss at position 3, because the top-weighted discount makes the tail
nearly invisible. Järvelin and Kekäläinen (2002) motivate graded,
position-discounted gain for exactly this reason; Joachims (2002) shows
how click-based online variants compound through position bias.

The trade, named: a suite plus a rank-gap audit costs measurement depth —
more labels, more curves, more review — and the alternative is a single
leaderboard metric that the ranking team will optimize and therefore
game. The metric decides what the team optimizes next, so the divergence
between leaderboards is the signal that someone must state which ranking
the users actually need; the product owner, not the ranker, resolves it.

## Who owns the loop

The metric decides what the team optimizes next; someone must own the
choice and its blind spot:

- **The evaluation or relevance team** owns the metric suite: graded
  labels, per-position NDCG@k curves, and the rank-gap audit that names
  which metric each ranking exploits. It owns the measurement, and the
  when-the-metric-is-gamed detour is its failure mode.
- **The ranking team** owns the objective that the metric selects
  between: pointwise vs pairwise vs listwise, and the risk that a
  ranker tunes to the leaderboard metric rather than to relevance. It
  owns the model, and the audit's METRIC DIVERGENCE verdict is its
  signal.
- **The product or search owner** owns what the metric must serve:
  whether the page goal is first-hit precision, coverage, or graded
  relevance across the list. It owns the metric choice itself, and it
  resolves a divergence by stating which ranking the users need.

When the ownership is implicit, the ranking team optimizes MRR, the
evaluation team reports NDCG, and nobody owns the disagreement — so a
first-hit gamer ships as "perfect" on the leaderboard metric while the
users see a page with one good result and nothing after it.

## Evidence boundary

The executed metrics over four hand-built graded rankings (illustrative).
It demonstrates the metric properties; real search evaluation also needs
relevance labels from humans or clicks, which this stage does not model.

## Check your mental model

Answer each before opening it.

**1. Why is MRR identical for "one good hit" and "good spread"?**

<details>
<summary>Answer</summary>

Because MRR only looks at the first relevant position. Both A and B have
their first relevant hit at position 1, so both score 1.0000 — MRR cannot
see that B keeps delivering after the first hit while A stops. That is the
metric's blind spot: it rewards a single early hit and ignores the rest
of the list.

</details>

**2. What does the D row (reversed) prove about NDCG?**

<details>
<summary>Answer</summary>

That NDCG is sensitive to ordering, not just presence. D has the same
grades as B but in reverse, and scores 0.2750 against B's 0.8140 — the
top-weighted discount punishes putting relevant items low. That ordering
sensitivity is exactly what a ranking metric must have, which is why NDCG
is the search analogue of the mission's nDCG@10 primary metric.

</details>

**3. Why does the audit report rank gaps instead of just both scores?**

<details>
<summary>Answer</summary>

Because the gap is the disagreement that matters. MRR ties five rankings
at 1.0000; the raw scores look identical, and only the leaderboard
positions reveal that NDCG separates those same five across five ranks.
The gap per ranking names which metric each ranking exploits — the
first-hit gamer moves four positions — which is the case-finding that
tells the team where the leaderboard can be gamed.

</details>

## Next

This closes the search track. Forward to [stage 14 — ad auction](../../ads/14-ad-auction/)
where a paid item competes for the same slot.

A detour from here: [the metric chooses the winner](when-mrr-and-ndcg-disagree/) — the executed metrics read: three rankings score MRR 1.0 while NDCG separates them, MRR's blind spot below the first hit.

Another detour: [NDCG@1 is a different claim than NDCG@5](when-the-k-is-small/) — the executed k-sweep read: the same ranking is 0.000 at @1 and 0.546 at @5, so k is part of the evaluation contract.

A third detour: [the metric is gamed](when-the-metric-is-gamed/) — the executed read: an engineered mrr gamer ties the honest spread at MRR 1.0000 while NDCG falls to 0.7519, and an ndcg gamer normalizes to 1.0000 with an empty tail, so concentration beats coverage when one metric picks the winner.
