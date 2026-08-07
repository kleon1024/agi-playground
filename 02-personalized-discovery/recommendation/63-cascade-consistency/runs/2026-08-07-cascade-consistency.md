# Run: 63 — cascade consistency

- **Command:** `uv run python core/cascade_consistency.py` (from
  `02-personalized-discovery/recommendation/63-cascade-consistency/`)
- **Config:** 1,500-item catalogue, pre-rank cut at 100, final top-20;
  a click-optimized pre-rank vs one distilled from the final ranker's soft
  scores. Deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.19s
- **Cost:** \$0
- **Metrics:**
  - CTR-only pre-rank: top-20 recall 0.35, final NDCG 0.967
  - distilled pre-rank: top-20 recall 1.00, final NDCG 1.000

The full printed read, reproduced verbatim on 2026-08-07:

```text
cascade consistency, read (pre-rank cut of 100 of 1500):
  ctr-only pre-rank  top-20 recall 0.35   final ndcg 0.967
  distilled pre-rank top-20 recall 1.00   final ndcg 1.000

reading: a pre-rank that optimizes clicks quietly discards the
transaction-heavy items the final ranker would have surfaced, and
the expensive ranker can only re-rank survivors. distilling the
final score into the pre-rank — as a soft label instead of a click
label — keeps the top of the final ranking inside the cut, which is
the metric that actually matters for the cascade.
```
