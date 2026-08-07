# Run — the stratified seesaw audit over the emitted cohort

**Date:** 2026-08-07
**Command:** `uv run python prod/seesaw_audit.py /tmp/seesaw-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas 3.0.5.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

The core run reports aggregate AUCs. This audit reads the emitted cohort
envelope and answers the case-finding question: where does the seesaw show
up? It stratifies the AUC matrix by slice and task for the naive and the
slice-weighted model, and checks whether the naive click head's scores are
calibrated probabilities by decile.

## Output

```
auc-label seesaw audit over the 640-row test cohort:

naive model, stratified AUC matrix:
  slice  task    rows  positives    auc
  head   click   325   197        0.644
  head   buy     325   30         0.710
  tail   click   315   87         0.662
  tail   buy     315   18         0.698
  aggregate: click 0.726, buy 0.716

slice-weighted model, stratified AUC matrix:
  slice  task    rows  positives    auc
  head   click   325   197        0.630
  head   buy     325   30         0.778
  tail   click   315   87         0.706
  tail   buy     315   18         0.782
  aggregate: click 0.723, buy 0.781

naive click head, per-decile calibration:
  decile   mean p  actual rate
  0       0.191   0.172
  1       0.251   0.141
  2       0.302   0.375
  3       0.353   0.328
  4       0.400   0.438
  5       0.461   0.406
  6       0.513   0.562
  7       0.561   0.547
  8       0.628   0.641
  9       0.723   0.828
  slope 1.188, intercept -0.077 (a slope of 1.0 is a calibrated probability)

verdict: AGGREGATE AUC HIDES THE TAIL SLICE TRADE --
slice weighting moves tail click AUC 0.662 to 0.706 while head click AUC falls 0.644 to 0.630, and the
aggregate click AUC only moves 0.726 to 0.723. the aggregate number hides the
reallocation; ranking on it alone ships a head model and
calls the tail loss noise.
```

## Notes

- The verdict is the stage's case-finding: the aggregate click AUC says
  "flat" while the tail slice gained 0.662 to 0.706 and the head slice
  paid 0.644 to 0.630. A model owner watching only the aggregate cannot
  tell whether the tail is being bought or sold.
- The naive click head's calibration slope is 1.188 at an intercept of
  -0.077: ranking order is preserved, but the score is not a probability,
  which breaks every downstream pCTR consumer (stage 05's value tree
  multiplies it). The `when-the-second-model-costs` detour repairs the
  mapping with temperature scaling and measures the second model's cost.
- The seesaw is only visible when the metric is stratified by slice and
  task; the per-decile calibration read is the third axis the audit adds.
