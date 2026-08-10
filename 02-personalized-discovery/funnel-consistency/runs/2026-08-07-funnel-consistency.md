# Run: 62 — funnel consistency

- **Command:** `uv run python core/funnel_consistency.py` (from
  `02-personalized-discovery/recommendation/62-funnel-consistency/`)
- **Config:** a head trained on clicked impressions read as a marginal
  (broken) vs the chained read (marginal click x conditional order),
  evaluated on 1,000 held-out impressions. Deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.40s
- **Cost:** \$0
- **Metrics:**
  - broken read: p(order) > p(click) on 649/1,000 impressions; order log-loss
    0.672
  - chained read: order log-loss 0.501; 0 violations by construction

The full printed read, reproduced verbatim on 2026-08-07:

```text
funnel consistency, read (conditional-as-marginal vs chained):
  broken read: p(order)>p(click) on 649/1000 held-out impressions
  broken read  order logloss 0.672
  chained read order logloss 0.501  (violations: 0 by construction)

reading: the head trained on clicked impressions estimates
p(order|click), and using it as p(order|impression) overstates the
marginal, so the pipeline reports an order probability above a click
probability. the chained read multiplies the marginal click
probability by the conditional, which keeps monotonicity structural
and recovers the marginal the downstream stage actually blends.
```
