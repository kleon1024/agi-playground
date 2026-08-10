# Run — the metric-divergence audit over the graded rankings

**Date:** 2026-08-07
**Command:** `uv run python core/search_eval.py --emit-log /tmp/eval-envelope.json` then `uv run python prod/eval_audit.py /tmp/eval-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib and pandas 3.0.5.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Build both leaderboards over the graded rankings and measure the rank
gap per ranking — the case-finding that shows which metric each ranking
exploits, and how a leaderboard inherits a metric's blind spot.

## Output

```
metric-divergence audit over the graded rankings:
  ranking                 NDCG    rank   MRR    rank   gap
  A: one good hit early    1.0000   1      1.0000   1      0
  B: good spread           0.8140   4      1.0000   1      3
  C: good at top           1.0000   1      1.0000   1      0
  D: reversed              0.2750   7      0.2500   7      0
  F: first-hit gamer       0.7519   5      1.0000   1      4
  G: ndcg gamer            0.8750   3      1.0000   1      2
  H: spread, early miss    0.5831   6      0.5000   6      0

verdict: METRIC DIVERGENCE -- 3 of 7
rankings move at least two leaderboard positions by metric
(B: good spread, F: first-hit gamer, G: ndcg gamer). MRR ties 5 rankings as joint best
that NDCG separates across the same five; the first-hit
gamer is MRR-perfect and NDCG-fifth. A leaderboard
that picks a winner by one metric is picking among rankings
the other metric ranks differently — report both, and audit
per position, because the metric being optimized is the one
that gets gamed.
```

## Notes

- Ranks are competition-style: tied metric values share the best rank.
  MRR ties five rankings at 1.0 that NDCG separates across five ranks;
  the first-hit gamer F is MRR-joint-best and NDCG-fifth, and the
  good-spread B is MRR-joint-best and NDCG-fourth.
- The audit cohort adds three rankings to the stage's four (F: a
  mediocre hit placed first; G: top-heavy; H: spread with an early
  miss). Järvelin and Kekäläinen, "Cumulated gain-based evaluation of
  IR techniques", ACM TOIS 20(4), 2002, is the source for graded,
  position-discounted gain; Joachims, "Optimizing Search Engines Using
  Clickthrough Data", KDD 2002, is why online click-based variants of
  the same games compound through position bias.
