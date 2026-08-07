---
status: verified
level: applied
base: none
verified: 2026-08-07
---

# Does a policy trained on expert demos imitate well outside the training set?

**Goal:** collect expert state-action pairs on 60 training scenarios, train
a small MLP to predict steer and throttle from the render, and measure
held-out imitation accuracy on frames the expert visits in 50 eval
scenarios — with a majority-action baseline so an imbalanced action
distribution cannot be mistaken for learning.

**Why this stage exists.** Imitation accuracy is the metric almost every
behavior-cloning writeup reports, and it is the wrong one to stop at. But it
is the right one to start with: if the policy cannot reproduce the expert's
actions on states the expert itself visited, nothing downstream is worth
measuring. This stage establishes that baseline honestly, then stage 04
measures the harder question — whether the same actions still work when the
policy's own mistakes move the car off the expert's path.

## What you build

`core/clone.py` — a 140k-parameter MLP (1024 -> 128 -> 64, two heads) trained
with cross-entropy on steer and throttle jointly:

- **Demos.** `collect_demos` rolls out the expert on train seeds 0-59 and
  records every (render, steer, throttle) triple — 8,366 frames, dominated
  by straight-road frames, which matters below.
- **Training.** 20 epochs, batch 256, Adam at 1e-3; a single CPU run.
- **Evaluation.** Held-out frames from eval seeds 100-149 (7,432 frames),
  actions compared to the expert's at the same state.

## What we measured

```bash
cd 09-autonomous-driving/03-behavior-cloning/core
python clone.py
```

| Metric | Cloned policy | Majority baseline |
|---|---|---|
| Steer accuracy | 0.883 | 0.740 |
| Throttle accuracy | 0.866 | 0.846 |
| Joint accuracy | 0.772 | — |
| Training wall-clock | 2.0s | — |

The model beats the majority baseline on steering (0.88 vs 0.74) — it
learned something about lane geometry — but the joint figure hides the
structure of the failure: dodge frames are a small minority of the demos,
and the model's steer head returns 0 wherever it is uncertain, which is
exactly where dodging would have been required. That imbalance is stage 04's
problem: open-loop accuracy rewards reproducing dominant actions, and the
in-loop test is where that strategy stops paying.

## Evidence boundary

This is open-loop imitation on expert states. It deliberately does not
measure whether the policy drives — a policy that perfectly matches the
expert on every held-out frame can still crash in the loop. That test is
stage 04, and the policy artifact trained here is the exact one evaluated
there. Numbers trace to
[`runs/2026-08-07-clone.json`](runs/2026-08-07-clone.json).
