# Run — the AUC-label seesaw, executed on the shared trunk

**Date:** 2026-08-07
**Command:** `uv run python core/seesaw.py --emit-log /tmp/seesaw-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 8.4s (3 variants x 60 epochs over 2,560 train rows).
**Cost:** \$0 (local lane).

## Purpose

Stage 64 asks which slice and which task silently pay for the objective the
model is visibly optimizing. This run trains a naive shared bottom, a
slice-weighted variant, and a gated (MMoE-lite) trunk on the same synthetic
cohort and reads per-task AUC — the two tasks (click and buy) and the two
head/tail slices that share one trunk.

## Output

```
auc-label seesaw, read (click vs buy, head vs tail):
  model               click auc buy auc
  naive shared bottom     0.726   0.716
  slice-weighted          0.723   0.781
  gated (mmoe-lite)       0.725   0.653
  click positives: head 762, tail 359
  buy positives in train: 136 of 2560

reading: head rows are denser and higher-signal, so the naive
gradient fits the head's click signal and the tail slice pays:
slice-weighting lifts the tail (and the buy task) at a small
head cost, while the aggregate click AUC barely moves. gating
does not automatically win -- on this cohort the explicit
slice weighting beats it. the seesaw is only visible when the
metric is stratified by slice and task.
```

## Notes

- The aggregate click AUC moves 0.726 to 0.723 under slice weighting —
  a number a dashboard would call flat — while the per-slice audit
  shows the tail trade beneath it.
- Gating (MMoE-lite) does not win here: buy AUC 0.653 against 0.781 for
  explicit slice weighting. The gate's win condition is task
  disagreement, which stage 61's detour `when-gating-does-not-help`
  measures; on this cohort the explicit weight beats the structure.
- The envelope written to `/tmp/seesaw-envelope.json` feeds
  `prod/seesaw_audit.py`, whose stratified verdict is the actual
  case-finding for this stage (see the audit run record).
