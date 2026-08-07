# Run — when warm start beats from scratch, executed on the transfer read

**Date:** 2026-08-07
**Command:** `uv run python core/warm_start.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 8.7s (3 variants x 30-60 epochs).
**Cost:** \$0 (local lane).

## Purpose

The cold-item slice has five train positives — a ranker trained there from
scratch is fitting noise. The natural fix is transfer: pre-train the trunk
on a dense task and fine-tune on the cold rows. This detour tests two
source tasks — clicks and head-slice purchases — and reads which one
actually transfers.

## Output

```
  cold rows: 3706 train, 936 test; 87 train positives
when warm start beats from scratch, read (cold slices):
  model                   cold-slice buy auc
  from scratch                       0.740
  from click task                    0.659
  from head-slice buy                0.786

reading: warm start is not automatic. the click task's trunk
is dominated by activity -- the signal that drives clicks, not
purchases -- so pre-training on it and fine-tuning on the cold
rows imports a misaligned representation and loses to scratch.
the same objective on the dense head slice is the aligned
source: it shares buy's drivers, so the fine-tune beats
scratch. the transfer test is source-task alignment, measured
per slice -- never assumed from the task names.
```

## Notes

- Warm start is not automatic: pre-training on clicks and fine-tuning on
  the cold rows (0.659) loses to training from scratch (0.740), because
  the click task's trunk is activity-dominated — the signal that drives
  clicks, not purchases.
- The aligned source wins: fine-tuning from the dense head slice's buy
  task (0.786) beats scratch (0.740), because it shares buy's drivers.
- The transfer test is source-task alignment, measured per slice — never
  assumed from the task names. This is the same shape as the warm-start
  prior literature (Yi et al., RecSys 2019, on sampling bias in YouTube
  recommendation labels) in miniature: what transfers is the signal
  distribution, not the task label.
