# Run — negative transfer grid: shared trunk vs single-task, balanced or not

**Date:** 2026-08-06
**Command:** `uv run python core/transfer_grid.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; reuses the stage's `fine_rank.py`
(the single-task loop mirrors its train_step math for one task).
**Wall-clock:** 1.2s (8 cells x 40 epochs).
**Cost:** \$0 (local lane).

## Purpose

Stage 04's shared-trunk model has one head per task. This run measures
transfer directly: for each objective, does training the trunk on ALL tasks
beat training it on that task alone, under naive and balanced weighting?

## Output

```
task           balanced   multi   single  transfer
click             False   0.852    0.889    -0.037
completion        False   0.838    0.861    -0.023
satisfaction      False   0.707    0.657    +0.051
dwell             False   0.000    0.000    +0.000
click              True   0.890    0.889    +0.001
completion         True   0.860    0.861    -0.001
satisfaction       True   0.616    0.657    -0.040
```

## Notes

- Negative transfer is real and per-task: in naive mode the shared trunk
  hurts click (-0.037) and completion (-0.023) while satisfaction gains
  (+0.051). The dwell row is excluded from the reading — its target is
  continuous seconds, and pairwise_accuracy is a binary metric, so 0.000 is
  the metric's None, not a result.
- The balanced weighting changes WHICH tasks transfer negatively: click and
  completion recover (near zero), satisfaction flips to -0.040. The
  transfer pattern is weighting-dependent, which is the stage's recorded
  naive-vs-scale-normalized claim re-measured on the transfer grid.
- Single seed per cell, 200 examples, 40 epochs: the directions are the
  finding, not the exact magnitudes.
