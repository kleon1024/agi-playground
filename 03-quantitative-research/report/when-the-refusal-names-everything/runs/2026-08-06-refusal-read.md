# Run — the refusal that names everything, re-run and grouped

**Date:** 2026-08-06
**Command:** `uv run python core/refusal_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.05s (re-runs the stage's own report against current state).
**Cost:** \$0 (local lane).

## Purpose

Stage 05's honest current state is CANNOT DETERMINE. This run re-runs the
stage's own report against the real current state (no committed outcome
artifact) and groups the 18 named missing inputs, so the refusal reads as a
checklist.

## Output

```
VERDICT: CANNOT DETERMINE
This report will not guess. The following inputs are missing:
  - baselines.buy_and_hold.sharpe_net_folds (passive-floor baseline, per fold)
  - baselines.buy_and_hold.max_drawdown.depth
  - baselines.momentum_12_1.sharpe_net_folds (the baseline that has to be beaten)
  - candidate.sharpe_net_folds (the number the primary metric is decided on)
  - candidate.sharpe_gross_folds (required beside net)
  - candidate.deflated_sharpe / _significance / n_variants_searched
  - candidate.max_drawdown.depth / max_position_pct_of_adv
  - candidate.point_in_time_violations / universe_survivorship_bias_free
  - cost.data_and_compute_usd_per_fold / modeled_txn_cost_bps
  - cost.modeled_impact_participation_rate
  - latency.p50_ms / latency.p95_ms
  - regimes (the mandatory regime-level failure-case breakdown)
```

## Notes

- The refusal is the stage's real current-state output; no outcome artifact
  exists because no stage has yet produced one.
- Grouped, the 18 inputs are 5 baselines/candidate evidence classes, 3 cost
  numbers, 2 latency numbers, and the regimes breakdown — the same shape
  `mission.yaml`'s acceptance contract demands.
