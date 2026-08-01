# Cross-endpoint analysis over stages 01, 03, 04's existing results

No new training. This run reads the three real Tox21 comparisons this
mission already produced — stage 01 (SR-MMP), stage 03 (NR-PPAR-gamma), and
stage 04 (NR-ER) — directly from their committed `data/split_summary.json`
and `runs/*-seed{0,1,2}.json` files, and asks whether any one simple variable
explains the pattern across the three.

## Command

```bash
cd missions/09-bio-pharma-modeling
uv run python 05-cross-endpoint-analysis/core/analyze_cross_endpoint.py
```

## Environment

| | |
|---|---|
| Machine | Apple silicon laptop, macOS 24.6.0, arm64 |
| Python | 3.12.9 (uv-managed) |
| Dependencies | standard library only (`json`, `statistics`) — no `torch`/`rdkit` needed, since nothing is retrained |
| Compute | CPU, sub-second, $0 |
| Inputs | `00-dataset-and-property/data/split_summary.json`, `03-second-endpoint/data/split_summary.json`, `04-third-endpoint/data/split_summary.json`, and each stage's six `runs/*-seed{0,1,2}.json` files (unmodified) |

## Output

```
Cross-endpoint analysis (n=3 Tox21 endpoints, no new training)
========================================================================
SR-MMP           n_train= 4643  pos_count= 689  pos_rate=0.1484  model=0.7312(+/-0.0159)  desc=0.8142(+/-0.0010)  gap=-0.0830  descriptor wins beyond spread
NR-PPAR-gamma    n_train= 5154  pos_count= 118  pos_rate=0.0229  model=0.6591(+/-0.0620)  desc=0.6554(+/-0.0044)  gap=+0.0037  inconclusive (gap inside spread)
NR-ER            n_train= 4949  pos_count= 628  pos_rate=0.1269  model=0.6679(+/-0.0227)  desc=0.6413(+/-0.0011)  gap=+0.0265  model wins beyond spread

Question 1: does positive-class count predict the TRAINED MODEL'S seed-to-seed variance?
  ranking positive_count -> model_auc_spread is: monotonic decreasing
  raw pairs (pos_count, model_spread): [(118, 0.062), (628, 0.0227), (689, 0.0159)]
  n=3 is too small for a correlation coefficient to mean anything; this is a
  monotonicity check on ranks only, reported as suggestive, not conclusive.

Question 2: does positive-class count predict WHICH approach wins (gap direction)?
  ranking positive_count -> gap(model-descriptor) is: not monotonic
  raw pairs (pos_count, gap): [(118, 0.0037), (628, 0.0265), (689, -0.083)]
  SR-MMP (pos_count=689) and NR-ER (pos_count=628) have similar positive
  counts but opposite winners (descriptor wins beyond spread vs model wins
  beyond spread) -- positive-class count alone does not explain who wins.

OVERALL: variance-vs-scarcity holds directionally (weak, n=3); win/loss
direction is NOT explained by positive-class count alone from this data.
```

Full structured output: [`2026-08-01-cross-endpoint-analysis.json`](2026-08-01-cross-endpoint-analysis.json).

## What n=3 does and does not support

The variance-vs-scarcity ranking (question 1) is monotonic across all three
points, consistent with stage 04's own verdict. It is still only a
monotonicity check over three ranks, not a correlation coefficient or a
significance test — no such statistic is reported or implied anywhere in
this stage, by design.

The win/loss direction (question 2) is the new, genuinely negative finding
this stage adds: SR-MMP and NR-ER have almost identical training positive
counts (689 vs 628) yet opposite winners, which rules out positive-class
count as a sufficient explanation for which approach wins on its own. This
stage does not propose a replacement variable — with three data points,
fitting a new explanatory variable to the same three outcomes would not be a
finding, it would be overfitting a hypothesis to its own evidence.
