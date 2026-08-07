---
status: verified
level: applied
base: scratch
label: Search ranking
verified: 2026-08-06
---

# Re-ordering the candidates: pointwise versus pairwise

**Question:** retrieval returns a candidate set, but the set is not the
answer. Search ranking re-orders it. This stage implements the two classic
formulations and asks which objective the metric actually rewards.

**Before this:** [stage 11 — search retrieval](../11-search-retrieval/)
for the candidate set, and [stage 04's fine-rank](../../shared/04-fine-rank/) for the
same idea in the recommendation funnel.

## The two formulations, executed

The run ([record](runs/2026-08-06-learning-to-rank.md)) executes both
rankers on the same eight-item labeled set:

| formulation | NDCG | order |
|---|---:|---|
| pointwise | 0.6209 | [0, 7, 1, 2, 3, 4, 6, 5] |
| pairwise | 0.5804 | [0, 7, 1, 4, 3, 2, 6, 5] |

## The mechanism, named

1. **Pointwise** — predict an absolute relevance score per item, rank by
   the score. The loss is squared error against the grade.
2. **Pairwise** — learn which of two items should rank first, by fitting
   a linear preference over item pairs. The loss is about comparison, not
   absolute score.

Both here are linear (least-squares fits) so the difference is purely in
the objective, not the model class. On small data they often agree — both
put items 0 and 7 first — but the NDCG gap (0.6209 vs 0.5804) is where
the formulations diverge.

## Why the metric is the arbiter

The two losses disagree on mid-list order (pointwise puts 2 before 3,
pairwise puts 4 before 3). Which is "right" is not decided by the loss —
it is decided by NDCG, the metric that measures what search actually
rewards: graded relevance, weighted to the top of the list. This is the
same lesson as stage 04's fine-rank applied to search: the objective and
the metric can be different, and the metric is the contract.

## How you find it: the label-consistency audit, executed

The ranker's output is only as stable as its labels, and ordinal grades
are judgments: a second grader can move a boundary item by one without
being wrong. The run ([record](runs/2026-08-07-search-ranking-audit.md))
emits the labeled set plus two re-graded batches, and the audit re-fits
the pairwise ranker on each:

| batch | direction disagreements | learned-pref flips | NDCG@A | NDCG@self |
|---|---:|---:|---:|---:|
| A (baseline) | 0 | 0 | 0.5804 | 0.5804 |
| B | 1 | 1 | 0.5727 | 0.5322 |
| C | 0 | 3 | 0.6209 | 0.7164 |

The verdict is PAIRWISE INCONSISTENT: NDCG@A swings 0.5727-0.6209 with
zero model change, and batch C flips three learned pair preferences
while changing no pair direction — a direction-only gate undercounts
label fragility. The flipped pairs are the smallest-margin pairs of the
clean fit (margins 0.017-0.056, the four smallest of 23), which is the
boundary concentration the when-the-label-is-relative detour measures.
Burges ("From RankNet to LambdaRank to LambdaMART: An Overview",
MSR-TR-2010-82, 2010) is the reference for why smooth list-aware losses
are the production answer to this sensitivity.

## Who owns the loop

The ranker learns from labels someone produced; the handoffs around the
label are where ranking fails:

- **The labeling or relevance team** owns the grades: the rubric, the
  grader agreement bar, and the redundant-grading policy that dilutes
  single-grader boundary noise. It owns the label fragility, and the
  when-the-label-is-relative detour is its failure mode.
- **The ranking team** owns the objective: pointwise vs pairwise vs
  listwise, the loss's sensitivity to the label set, and the margin-aware
  or LambdaRank-style variants when label noise is measured. It owns
  the fit, and the audit's PAIRWISE INCONSISTENT verdict is its signal.
- **The evaluation team** owns the frozen label set that NDCG is
  computed against. It owns the eval stability, and it is the team that
  must re-audit labels when a model "improves" without a model change.

When the ownership is implicit, the labeling team ships grades, the
ranking team tunes the loss, and nobody owns the boundary — so a
grader's one-grade move silently changes the offline leaderboard, and
the team celebrates or reverts a model that never changed.

## Evidence boundary

The executed rankers over an eight-item synthetic labeled set (two
features, grades 0-3, deterministic). It demonstrates the formulation
contrast; it does not claim one formulation always wins — the NDCG gap is
an instance, not a law.

## Check your mental model

Answer each before opening it.

**1. Why would pairwise ever lose to pointwise?**

<details>
<summary>Answer</summary>

Because pairwise optimizes comparisons, not absolute quality — and on a
small set the pairwise fit can be noisier than the pointwise one. The two
objectives measure different things: pointwise asks "how relevant is
this?" and pairwise asks "is A better than B?". Which better predicts the
metric is empirical, which is why the run reports NDCG for both instead
of asserting a winner.

</details>

**2. Why does NDCG, not the loss, decide the better ranker?**

<details>
<summary>Answer</summary>

Because the loss is a proxy and the metric is the contract. Squared error
or pairwise error can be minimized while the ranking the user sees is
worse, if the loss weights the wrong positions. NDCG is graded and
top-weighted — it matches what search actually rewards — so it is the
arbiter between formulations, exactly as the mission's own evaluation
discipline uses the declared metric over the trained loss.

</details>

**3. Why does the audit re-fit the ranker instead of diffing the grades?**

<details>
<summary>Answer</summary>

Because grade-order agreement between two grading passes is not ranker
agreement. Batch C changes no pair direction between graders, yet the
re-fitted ranker flips three learned preferences — the fit sees the whole
loss landscape, and small grade shifts re-weight every pair. A
direction-only consistency check would pass batch C and miss the
instability. The audit re-runs the model on each grading, which is how a
production team would catch a label-set-dependent leaderboard.

</details>

## Next

Forward to [stage 13 — search evaluation](../13-search-evaluation/) which
decides what "worked" means.

A detour from here: [the label that carries the position's bias](when-the-label-is-a-click/) — the executed exposure model read: observed click = relevance x exposure, so raw clicks teach position, not meaning.

Another detour: [where the formulation choice actually matters](when-the-list-is-longer/) — the executed sixteen-item run read: the pointwise/pairwise NDCG gap grows with list length, so the objective choice matters more as candidates grow.

A third detour: [the label that is relative](when-the-label-is-relative/) — the executed sweep read: 12 of 13 single grade flips leave the ranker unchanged while the smallest-margin boundary flip and two-flip re-gradings swing NDCG 0.5727-0.6209, so label fragility concentrates on the learned decision boundary.
