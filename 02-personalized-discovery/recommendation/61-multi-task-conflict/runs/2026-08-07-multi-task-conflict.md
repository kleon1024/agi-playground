# Run: 61 — multi-task conflict

- **Command:** `uv run python core/multitask_conflict.py` (from
  `02-personalized-discovery/recommendation/61-multi-task-conflict/`)
- **Config:** shared-bottom multi-task model with CTR (~10%) and purchase
  (~1%) tasks over 2,000 synthetic rows; three variants: naive shared bottom,
  gradient-balanced purchase loss, and a gated (MMoE-lite) trunk.
  Deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 6.49s
- **Cost:** \$0
- **Metrics:**
  - naive shared bottom: CTR AUC 0.582, buy AUC 0.461
  - gradient-balanced: CTR AUC 0.590, buy AUC 0.660
  - gated (MMoE-lite): CTR AUC 0.608, buy AUC 0.564
  - purchase positives in train: 31 of 2,000
  - final gradient norms: CTR 0.484 vs buy 0.076

The full printed read, reproduced verbatim on 2026-08-07:

```text
multi-task conflict, read (ctr ~10% vs purchase ~1%):
  model                ctr auc buy auc
  naive shared bottom    0.582   0.461
  gradient-balanced      0.590   0.660
  gated (mmoe-lite)      0.608   0.564
  purchase positives in train: 31 of 2000
  final gradient norms: ctr 0.484 vs buy 0.076

reading: the click loss pulls the shared trunk far harder than the
purchase loss, so the sparse task's representation is shaped by the
abundant task. balancing the purchase loss rescues the sparse task
outright; the gated trunk improves on naive without a hand-tuned
weight, landing between the two here. gating is the structural
answer that scales when the conflict is not one weight.
```
