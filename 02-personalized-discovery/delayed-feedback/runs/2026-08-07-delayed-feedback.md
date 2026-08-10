# Run: 57 — delayed feedback

- **Command:** `uv run python core/delayed_feedback.py` (from
  `02-personalized-discovery/recommendation/57-delayed-feedback/`)
- **Config:** 7-day label window, young snapshot (0.3-3d); mature-only,
  naive-all, and corrected (soft-label from the delay distribution and base
  rate) training schemes. 4,500 training rows. Deterministic seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.58s
- **Cost:** \$0
- **Metrics:**
  - mature-only: starved (no mature rows yet)
  - naive-all: conv AUC 0.666, mean predicted conversion on fresh traffic 0.092
  - corrected: conv AUC 0.672, mean predicted conversion on fresh traffic 0.142
  - true conversion-by-7 on fresh traffic: 0.132
  - in-flight converters in training rows: 581

The full printed read, reproduced verbatim on 2026-08-07:

```text
delayed feedback, read (window 7d, young snapshot 0.3-3d):
  mature-only  starved (no mature rows yet)
  naive-all    conv auc 0.666   pred on fresh 0.092
  corrected    conv auc 0.672   pred on fresh 0.142

training rows 4500, mature rows 0, in-flight converters 581
true conversion-by-7 on fresh traffic: 0.132
reading: with a young snapshot there is no mature set to wait for,
so mature-only is starved by definition. naive-all eats every
in-flight converter as a false negative and under-reads fresh
traffic — the CVR dip every launch sees. the corrected model keeps
all rows and gives censored rows a soft label from the delay
distribution and the base rate, so freshness stops costing scale.
```
