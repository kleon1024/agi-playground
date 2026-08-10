# Run — sparse labels, executed on the cold-slice buy model

**Date:** 2026-08-07
**Command:** `uv run python core/sparse_labels.py --emit-log /tmp/sparse-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 8.9s (3 variants x 60 epochs over 6,400 train rows).
**Cost:** \$0 (local lane).

## Purpose

Stage 65 asks what a buy objective learns on slices where purchase labels
are nearly absent. This run trains three variants on the cold (non-head)
rows — a buy-only model from scratch, a shared trunk that also fits clicks,
and a surrogate-trained model using an "engaged" label as the buy proxy —
and reads cold-slice buy AUC plus the label-density facts under them.

## Output

```
sparse labels, read (buy over cold slices):
  variant                  cold-slice buy auc
  cold-only, from scratch               0.678
  shared trunk (click+buy)              0.780
  surrogate (engaged)                   0.696
  buy positives in train: head 119, cold-user 74, cold-item 5
  in-flight purchases at snapshot 0.6d: 40

reading: a buy-only model trained where the labels exist is
starved on the cold-item slice -- five train positives cannot
shape a ranker, and the cold-only model is really a cold-user
model. the shared trunk borrows the click representation only
when the buy loss is balanced (stage 61); the surrogate label
fills the empty slice with positives at the cost of importing
the surrogate's noise into every predicted probability.
```

## Notes

- The density facts are the case-finding input: 119 buy positives in the
  head slice, 74 for cold users, 5 for cold items. Five positives cannot
  shape a ranker; the cold-only model's 0.678 is really a cold-user
  number averaged over a slice that includes 5-positive cold items.
- The shared trunk beats it (0.780) only when the buy loss is balanced —
  the stage 61 mechanism — otherwise the click task's gradient owns the
  representation.
- The surrogate fills the empty slice (0.696) at a price the
  `when-the-surrogate-label-bleeds` detour measures: probability meaning,
  not just ranking.
- The envelope written to `/tmp/sparse-envelope.json` feeds
  `prod/sparse_labels_audit.py`, whose per-slice interval report is the
  stage's actual verdict.
