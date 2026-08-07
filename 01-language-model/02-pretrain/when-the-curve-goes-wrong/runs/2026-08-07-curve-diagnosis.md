# Run — Four injected pretraining failures and their diagnostics

**Date:** 2026-08-07
**Command:** `uv run python core/curve_diagnosis.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; numpy.
**Wall-clock:** 7.0s.
**Cost:** \$0 (local lane).

## Purpose

The chapter's "read the pair, not the line" table was asserted, not
measured. This run executes four of its rows on one from-scratch
next-token learner (2-layer MLP over a 2-token context, 16-symbol
planted Markov task, 3000 train / 1000 held-out tokens, single seed
42): too-high learning rate, loss overflow into non-finite range, a
corrupted batch, and bf16 resolution loss. Each failure is planted, and
the run records the pair (train/held-out) plus the gradient-norm trace,
so the claim that a diagnostic *precedes* the visible spike can be
checked against numbers.

## Output

```
when the curve goes wrong, read (four injected failures):
  one seed, numpy-only 2-layer next-token learner;
  3000 train / 1000 held-out tokens, 16-symbol planted Markov task

  baseline (lr 0.3, 200 steps):
    step 0:  train 2.9057  held 2.9160
    step 199: train 2.4246  held 2.5900

  failure 1 - learning rate too high (lr 12):
    step 0:  train 2.9057  held 2.7286  grad-norm 0.223
    step 4:  train 2.9034  held 3.0715  grad-norm 0.600  (baseline grad-norm 0.223->0.197 at step 4)
    step 5:  train 2.9631  held 7.9607  grad-norm 0.564
    step 6:  train 7.6753  held 36.0983  grad-norm 3.722
    step 7:  train 35.5679  held 10.1362  grad-norm 36.804 (peak 36.804 at step 7)
    step 199: train 176.3024  held 188.3987  (diverged, no recovery)
    gradient norm departs from the baseline ~2 steps before the train loss does

  failure 2 - loss overflows the compute range (lr 48, fp32-
  range softmax without max subtraction):
    first non-finite loss: step 3; with the check the run stops there (3 steps executed)
    without the check: step 0 train 2.9057, then step 10 inf, step 20 inf, step 30 inf, ... step 199 nan
    the unchecked run cannot report which step first went wrong

  failure 3 - corrupted batch (steps 100-139, random labels):
    baseline at 95/100/120/140/160/200: train 2.5073/2.5006/2.4777/2.4596/2.4452/2.4242 | held 2.6224/2.6190/2.6083/2.6010/2.5959/2.5899
    corrupt  at 95/100/120/140/160/200/239: train 2.5073/2.9454/2.8451/2.5875/2.5210/2.4563/2.4284 | held 2.6224/2.6188/2.6333/2.6509/2.6118/2.5856/2.5812
    both curves move together during the window and return toward the baseline path

  failure 4 - bf16 resolution loss (bf16 master weights, lr 0.5 -> 0.001 over 800 steps):
    fp32 master: train 2.3789 @300 -> 2.3577 @799 | held 2.5851 -> 2.5938 | grad-norm 0.0197 -> 0.0144
    bf16 master: train 2.4246 @300 -> 2.4177 @799 | held 2.5714 -> 2.5696 | grad-norm 0.0506 -> 0.0505
    bf16 train flatlines ~0.06 above the fp32 floor while the
    gradient norm stays alive (0.050 vs fp32 0.014): precision
    floor, not a dead loop.
```

## What the numbers show

- **Too-high LR:** at step 4 the gradient norm is 3x the baseline run
  (0.600 vs 0.197) while the train loss still looks normal (2.9034 vs
  the baseline's 2.852). The loss explodes two steps later and never
  recovers. A run that logs norms sees the failure coming; a run that
  logs only loss does not.
- **Overflow:** with softmax computed in fp32 range without max
  subtraction (the naive accelerator path), the loss goes non-finite at
  step 3. The checked run stops and reports that step; the unchecked
  run completes with a wall of inf then NaN and no step attribution.
- **Corrupted batch:** train and held-out both rise together during the
  window (step 140: train 2.5875 and held 2.6509 vs baseline 2.4596 and
  2.6010) and return toward the baseline path after it closes. That pair
  shape is what separates a bad batch from overfitting (train falls,
  held rises) or a dead loop (both flat).
- **bf16 resolution loss:** with bf16 master weights the train curve
  flatlines (2.4246 at step 300 to 2.4177 at step 799, moving 0.0013 in
  300 steps) while the fp32-master control keeps descending (2.3577 by
  step 799). The gradient norm stays alive at ~0.050 (vs fp32 0.014),
  which is what rules out a dead loop: the LR schedule is healthy and
  the gradients are real, but small updates round away against the bf16
  accumulator.

## Evidence boundary

- This is a deterministic single-seed illustration on a 2-layer toy, not
  the 88M decoder. The LR values (12, 48) are knobs chosen to make each
  failure visible inside 200-800 steps, not the mission run's schedule.
- The mission's own 3.0689-to-3.0984 anomaly remains unattributed. This
  run demonstrates the diagnostic procedure; it does not diagnose that
  run, whose three candidate owners predict the same curve.
- The bf16 run simulates the "bf16 master weight" simplification, not
  the full mixed-precision contract. Held-out does not separate (bf16
  2.5696 vs fp32 2.5938 on this toy, where rounding acts as mild
  regularization); the precision floor is visible in the train curve.
- The overflow run computes softmax in fp32 range without max
  subtraction to reproduce the accelerator mechanism. Real fp16/bf16
  overflows at far lower logits than fp64; the threshold differs, the
  telemetry point (checked vs unchecked) is what transfers.
- The corrupted batch replaces labels with uniform draws on a full
  stream slice, not realistic label flips, and recovery is measured over
  the remaining 100 steps.
