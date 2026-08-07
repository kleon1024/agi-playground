# Run — the sparse-label audit over the emitted cohort

**Date:** 2026-08-07
**Command:** `uv run python prod/sparse_labels_audit.py /tmp/sparse-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas 3.0.5.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

The core run reports variant AUCs. This audit answers the case-finding
question: where is the label sparse, and can the numbers there decide
anything? It emits a per-slice label-density report, the delay
distribution of purchase labels, and per-slice buy AUC with bootstrap
5-95% intervals for the shared model.

## Output

```
sparse-label audit over the 1,600-row test cohort:

label-density report by slice:
  slice       rows  positives  positive rate
  head        659   30         0.0455
  cold-user   681   21         0.0308
  cold-item   260   2          0.0077

delay distribution of purchase labels:
  median 0.39d, p75 0.48d, p95 0.64d
  in-flight at snapshot 0.6d: 11% of purchases

shared model, per-slice buy AUC (bootstrap 5-95%):
  slice       rows  positives     auc    ci low   ci high
  head        659   30           0.752    0.678    0.822
  cold-user   681   21           0.745    0.667    0.823
  cold-item   260   2            0.773    0.500    0.957
  aggregate                                            0.769

verdict: THE AGGREGATE AUC IS A DENSE-SLICE NUMBER --
the aggregate buy AUC is 0.769, but the cold-item slice
carries a handful of positives and its 5-95% interval spans
chance; the number that ships is a head-and-cold-user number.
report per slice with its interval, and gate the cold-item
slice on a different signal (surrogate, exposure, content)
because its own labels cannot decide anything yet.
```

## Notes

- The cold-item slice carries 2 positives out of 260 test rows; its AUC
  interval is [0.500, 0.957] — it spans chance. The aggregate 0.769 is a
  head-and-cold-user number, and reporting it alone ships confidence the
  cold-item slice does not have.
- Delay matters to the density: purchases arrive with median 0.39d and
  p95 0.64d, so an 0.6-day snapshot still has 11% of purchases in
  flight — the label window (stage 57) is part of why the cold-item
  slice looks this sparse.
- The interval is the evaluation guardrail: widen the window, add
  surrogate or exposure labels, then re-check the slice's interval —
  not the aggregate — before the slice's own numbers can decide anything.
