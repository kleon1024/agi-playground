# Run — the served-k audit over the query log

**Date:** 2026-08-07
**Command:** `uv run python core/rerank_top_k.py --emit-log /tmp/rerank-envelope.json` then `uv run python prod/rerank_audit.py /tmp/rerank-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Compare the reranker's delta at the offline eval k (NDCG@10) with its
delta at the served page k (NDCG@3), stratified by head and tail — the
offline/online consistency check that catches a reranker approved at
@10 while hurting the @3 page.

## Output

```
served-k audit over the 20-query log:
  aggregate @10: first 0.710 -> rerank 0.790 (delta +0.080)
  aggregate @3:  first 0.875 -> rerank 0.860 (delta -0.015)

  stratum  queries  delta@10  delta@3  agree?
  head     10       +0.080    +0.050    yes
  tail     10       +0.080    -0.080    NO

verdict: SERVING-K DIVERGENCE -- the @10 experiment
approves the reranker (aggregate +0.080) while the
served @3 report says the page got worse (-0.015).
The entire loss is tail (-0.080 at @3 against +0.080
at @10): the reranker's fixes land in the middle of the
list, below the three served slots. Report at the served
k, audit per position, and slice the rerank experiment
by head and tail before shipping it.
```

## Notes

- The audit cohort is a 20-query log with first-stage and reranked
  NDCG@10 and NDCG@3 per query. Head queries improve on both surfaces
  (+0.080 at @10, +0.050 at @3); tail queries improve at @10 (+0.080)
  while degrading at @3 (-0.080).
- The aggregate tells both stories at once: @10 says "ship the
  reranker" (+0.080), @3 says "the page got worse" (-0.015). Two teams
  reporting at different k's reach opposite conclusions about the same
  change.
- The mechanism (per the when-the-gain-is-below-the-fold detour):
  reranker fixes land in the middle of the list, below the three served
  slots. Nogueira and Cho, "Passage Re-ranking with BERT",
  arXiv:1901.04085, 2019, is the cross-encoder reranker reference; the
  cost of that model is why the shortlist is short, and the served page
  shorter — the eval has to report at the served k.
