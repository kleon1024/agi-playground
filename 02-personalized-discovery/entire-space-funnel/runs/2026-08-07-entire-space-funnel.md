# Run: 56 — entire-space funnel

- **Command:** `uv run python core/entire_space.py` (from
  `02-personalized-discovery/recommendation/56-entire-space-funnel/`)
- **Config:** synthetic impressions with declared click rate and
  pay-given-click rate; a pay head trained on the clicked subset vs an
  ESMM-style CTCVR head trained on the full exposure space. Deterministic
  seed.
- **Hardware:** local Mac (CPU)
- **Wall-clock:** 0.70s
- **Cost:** \$0
- **Metrics:**
  - clicked-subset pay head: 705 positives, CVR AUC 0.735
  - full-space CTCVR head: 936 positives, CVR AUC 0.740

The full printed read, reproduced verbatim on 2026-08-07:

```text
entire-space funnel, read (CVR on clicked subset vs full space):
  clicked subset        positives   705   cvr auc 0.735
  entire space (ctcvr)  positives   936   cvr auc 0.740

reading: the clicked-only head sees a tenth of the positive
signal and a selection-biased training set; the full-space
CTCVR head labels every impression and keeps p_pay <= p_click
by construction, so it recovers the true conditional better.
```
