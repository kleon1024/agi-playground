# Run — the dead-code reset's trajectory, read from the recorded seeds

**Date:** 2026-08-06
**Command:** `uv run python core/reset_trajectory.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three recorded JSONs).
**Cost:** \$0 (local lane; the underlying training was stage 05's recorded
run).

## Purpose

Stage 05's recorded runs reset dead codes and ended healthy (64/64 usage in
all three seeds). This run reads their `reset_log` trajectories to answer
whether the reset is a one-time cure or a maintenance loop the training
keeps paying.

## Output

```
seed  total resets  first event  last event  final usage  eval MSE
   0          1893       50@  60     2000@   1      64/64     0.0187
   1          1848       50@  60     1950@   1      64/64     0.0172
   2          1388       50@  63     1550@   1      64/64     0.0173

reset events per 200-step window (seed 0):
  step    0- 200:  180 codes reset
  step  200- 400:  240 codes reset
  step  400- 600:  242 codes reset
  step  600- 800:  248 codes reset
  step  800-1000:  248 codes reset
  step 1000-1200:  248 codes reset
  step 1200-1400:  248 codes reset
  step 1400-1600:  221 codes reset
  step 1600-1800:   14 codes reset
  step 1800-2000:    3 codes reset
  step 2000-2200:    1 codes reset
```

## Notes

- The reset is a maintenance loop, not a cure: 1,388-1,893 codes are reset
  across each 2,000-step run, and the codebook keeps dying and being revived
  through roughly the first 1,400 steps (about 1.2 codes reset per step,
  sustained).
- The near-total collapse at step 50 (60-63 of 64 codes reset in one event)
  matches the codebook-collapse chapter's step-0 finding: the codebook
  starts dead and the reset has to drag it out.
- The codebook stabilizes only in the last ~400 steps (window resets fall
  248 -> 14 -> 3 -> 1), so "healthy usage 64/64" is a late-training steady
  state maintained by continuous resetting, not a state the codebook
  reached on its own.
- The reset count is the maintenance cost the stage 06 factorial exists to
  reduce: if EMA (or reset+EMA) keeps codes alive, the total reset load
  should drop; that comparison is stage 06's verdict.
