# Run — the fusion-weight audit over the query log

**Date:** 2026-08-07
**Command:** `uv run python core/fuse_sets.py --emit-log /tmp/fusion-envelope.json` then `uv run python prod/fusion_audit.py /tmp/fusion-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stratify the fusion-weight swing by head and tail — the case-finding
that shows where the fusion weight actually decides, and whether a
flat aggregate weight sweep is hiding a tail decision.

## Output

```
fusion-weight audit over the 20-query log:
  stratum  queries  NDCG@w0  NDCG@w0.5  NDCG@w1   mean swing
  head     10       0.900   0.920     0.900   0.020
  tail     10       0.557   0.794     0.451   0.343

verdict: WEIGHT SWING CONCENTRATED IN THE TAIL -- the
weight moves tail NDCG by 0.34 on average
(0.45-0.80 range) against 0.02 on head.
A head-dominated sweep looks flat, so the team concludes
the weight does not matter — but for the tail it decides
which matcher wins. Tune the weight on the tail, not the
aggregate, and report the swing per stratum.
```

## Notes

- The audit cohort is a 20-query log with the fused-list NDCG at three
  weights: 0.0 (lexical only), 0.5 (balanced), 1.0 (dense only). Head
  queries are covered by either matcher (swing 0.020); tail queries
  swing 0.343, from 0.451 at dense-only to 0.794 at balanced.
- The trap this verdict names: a head-dominated weight sweep looks
  flat, so the conclusion "the fusion weight does not matter" gets
  shipped — while the tail, where the weight is the decision, is
  silently served whichever matcher the aggregate picked.
- Cormack, Clarke and Büttcher, "Reciprocal Rank Fusion Outperforms
  Condorcet and Individual Rank Learning Methods", SIGIR 2009, is the
  source for the RRF mechanism; this audit is the operational check
  that the fusion's trust decision is query-dependent, which is what
  the head/tail split exposes.
