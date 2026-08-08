---
status: verified
level: applied
base: scratch
label: When the metric is gamed
verified: 2026-08-07
---

# The ranking that concentrates relevance where the metric cannot see

**Question:** [stage 13's metrics](../) have blind spots, and a system
can place relevance exactly where the metric does not look. This chapter
builds two rankings engineered to win one metric each and measures what
the other metric says about them.

**Before this:** [stage 13 — search evaluation](../) for NDCG and MRR,
and the stage's metric-divergence [audit run](../runs/2026-08-07-search-evaluation-audit.md)
that finds the exploited rankings first.

## The games, executed

The run ([record](runs/2026-08-07-metric-game-read.md)) scores four
rankings by both metrics:

| ranking | grades | NDCG@5 | MRR |
|---|---|---:|---:|
| honest spread | 1, 2, 2, 1, 0 | 0.8140 | 1.0000 |
| mrr gamer | 1, 3, 3, 3, 3 | 0.7519 | 1.0000 |
| ndcg gamer | 3, 2, 2, 0, 0 | 1.0000 | 1.0000 |
| both gamed | 3, 0, 0, 0, 0 | 1.0000 | 1.0000 |

## Two findings

**The mrr gamer ties the honest spread while being worse by any graded
measure.** Placing one grade-1 hit at position 1 scores MRR 1.0000 —
identical to the honest spread's 1.0000 — because MRR is binary: a
grade-1 near-miss at the top is worth the same as a grade-3 perfect
match, and everything after the first hit is ignored. NDCG is the only
row that separates them: 0.7519 against 0.8140. Järvelin and Kekäläinen
("Cumulated gain-based evaluation of IR techniques", ACM TOIS 20(4),
2002) introduced graded, position-discounted gain precisely because
binary rank-only measures could be gamed this way.

**The ndcg gamer normalizes to 1.0 with an empty tail.** A sorted top-3
is the ideal of its own grades, so NDCG says 1.0000 while positions 4-5
are zero — the top-weighted discount makes the tail nearly invisible.
The stage's own C row shows the same effect. Online, the games compound:
click-based metrics inherit position bias, so a system optimizing
click-through learns to exploit it (Joachims, "Optimizing Search Engines
Using Clickthrough Data", KDD 2002). The fix is the suite plus
per-position NDCG@k curves — report several metrics and check the
rank-gap audit, because the metric being optimized is the one that gets
gamed.

## The fix and its trade

The fix is the metric suite plus per-position NDCG@k curves, checked
against a rank-gap audit — because the metric being optimized is the one
that gets gamed. The executed games price the failure: the mrr gamer
(grades 1, 3, 3, 3, 3) scores MRR 1.0000, identical to the honest
spread's 1.0000, while NDCG is the only row that separates them (0.7519
versus 0.8140) — MRR is binary, a grade-1 near-miss at the top is worth
the same as a grade-3 perfect match, and everything after the first hit
is ignored. The ndcg gamer (3, 2, 2, 0, 0) normalizes to 1.0000 with an
empty tail because a sorted top-3 is the ideal of its own grades.

The trade, named: the suite costs more labels and per-position review,
and even then the games compound online — click-based metrics inherit
position bias, so a system optimizing click-through learns to exploit it
(Joachims, KDD 2002). The rank-gap audit is the piece that cannot be
skipped: it names which metric each ranking exploits before the
leaderboard certifies a gamer as perfect.

## Who owns the loop

- **The evaluation and relevance team** owns the suite, the per-position
  curves, and the rank-gap audit — the gamer detection is their signal.
- **The ranking team** owns the objective risk: tuning to the
  leaderboard metric rather than to relevance is a model-team failure
  the audit exists to expose.
- **The product and search owner** owns what the metric must serve —
  first-hit precision, coverage, or graded relevance — and resolves a
  divergence by stating which ranking the users need.

## Evidence boundary

The four rankings are hand-engineered grade lists (illustrative,
deterministic). They demonstrate the concentration mechanism — where
each metric's discount goes to zero — not a real system's gaming rate,
which needs a production ranking and its labels.

## Check your mental model

Answer each before opening it.

**1. Why does the mrr gamer score exactly the same MRR as the honest
spread?**

<details>
<summary>Answer</summary>

Because MRR looks only at the position of the first relevant hit. Both
rankings have a relevant document at position 1, so both score 1.0000 —
MRR never inspects the grade of that hit or anything after it. The game
works because binary relevance at position 1 is all MRR can see.

</details>

**2. What does the ndcg gamer's 1.0000 actually prove?**

<details>
<summary>Answer</summary>

That NDCG normalizes against the ideal of the returned list, so any
sorted list scores 1.0000 regardless of what is missing. The top-3 is
sorted and the empty tail is discounted into invisibility. A perfect
NDCG is a statement about ordering within the list, not about whether
the list covers what the user needed — which is why the audit reports
per-position curves and several metrics together.

</details>

## Next

Back to [stage 13](../), or forward to
[stage 14 — ad auction](../../../ads/14-ad-auction/) where a paid item
competes for the same slot.
