# Run — when the aggregate AUC lies, executed on the bootstrap-interval read

**Date:** 2026-08-07
**Command:** `uv run python core/aggregate_lies.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 4.2s (70 epochs + 120 bootstrap draws per k).
**Cost:** \$0 (local lane).

## Purpose

The stage-65 audit reports a cold-item slice whose 5-95% interval spans
chance. This detour turns that into arithmetic: how many positives does a
slice need before its AUC interval stops spanning chance? It subsamples
the dense head slice (659 rows, 30 positives) at increasing positive
counts and reads the bootstrap 10-90% interval at each size.

## Output

```
when the aggregate AUC lies, read (bootstrap interval):
  positives       10-90 pct interval
  2         0.000 .. 1.000 (w=1.000)
  5         0.250 .. 1.000 (w=0.750)
  10        0.222 .. 1.000 (w=0.778)
  20        0.316 .. 1.000 (w=0.684)
  30        0.414 .. 0.931 (w=0.517)

reading: with two positives the interval is so wide it spans
chance -- no modeling choice changes that, only the label
supply does. the aggregate number is not lying, it is just
measured where the labels are. the guardrail for a sparse
slice is a data decision: longer window, surrogate labels,
or exposure data, gated on the slice's interval, not the
aggregate AUC.
```

## Notes

- With 2 positives the interval is [0.000, 1.000] — the read cannot tell
  a coin flip from a perfect ranker. The interval only starts to narrow
  around 20-30 positives (width 0.684 to 0.517).
- The interval width is a label-supply fact, not a model fact: no
  architecture, loss, or gating choice changes it, which is why the
  stage's guardrail is a data decision (longer window, surrogate labels,
  exposure data) gated on the slice's interval.
- The aggregate AUC is not lying — it is measured where the labels are.
  Reporting it alone is the defect; the fix is to report per-slice with
  its interval.
