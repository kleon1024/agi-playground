# Run — the stale-embedding audit over the query log

**Date:** 2026-08-07
**Command:** `uv run python core/two_tower.py --emit-log /tmp/dense-envelope.json` then `uv run python prod/dense_audit.py /tmp/dense-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Compare recall@5 against fresh and stale doc embeddings, stratified by
head and tail — the offline/online consistency check that shows which
queries survive a stale index and where embedding freshness has to be
decided.

## Output

```
stale-embedding audit over the 20-query log:
  aggregate recall@5: fresh 1.000 -> stale 0.670 (gap -0.330)

  stratum  queries  fresh  stale   gap
  head     10       1.000  0.940   -0.060
  tail     10       1.000  0.400   -0.600

verdict: STALE EMBEDDING DIVERGES IN THE TAIL -- the
fresh-versus-stale gap is -0.600 on tail queries
against -0.060 on head. Head queries survive a
stale index; tail queries lose most of their recall. An
aggregate consistency check reports the mean gap and
approves the stale snapshot; the stratified view says the
tail is where embedding freshness has to be decided.
```

## Notes

- The audit cohort is a 20-query log: 10 head and 10 tail, each with a
  perfect fresh recall@5 (1.000) and a stale-snapshot recall@5. Head
  queries lose 0.060; tail queries lose 0.600. The aggregate gap of
  -0.330 hides the tail collapse.
- The mechanism: between embedding runs the doc vectors drift, and the
  queries that lose the most are the rare, low-training tail — exactly
  the ones a two-tower model represents worst. Huang et al.,
  "Embedding-based Retrieval in Facebook Search", KDD 2020, pages
  2553-2561, is the industrial reference for serving embedding
  retrieval in search, including the training-data choices (hard
  negative sampling between ranks 101-500) that determine how well the
  tail is represented in the first place.
- The decision that follows: embedding freshness is a tail decision.
  An aggregate consistency check approves the stale snapshot; the
  stratified view forces a choice — refresh the index for the tail, or
  fall back to lexical/hybrid for the queries the stale vectors cannot
  serve.
