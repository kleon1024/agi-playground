---
status: verified
level: applied
base: none
verified: 2026-08-07
---

# Can the render be read at all, by hand and by learning?

**Goal:** recover the two quantities a controller needs — lateral offset from
the lane center and distance to the nearest obstacle ahead — from the 32x32
render, once with a hand-built estimator and once with a small learned
network, both measured against ground truth from the simulator state.

**Why this stage exists.** A policy that steers from pixels can only be as
good as the information the pixels carry. If the render leaks nothing, no
controller trained on it will drive; if it leaks everything, the perception
problem is solved before the control problem starts. Measuring the leak
first — with a hand estimator as the honest baseline — is what separates
"the model learned to drive" from "the model got lucky on a dataset whose
geometry was trivial."

## What you build

`core/perception.py` — two estimators plus an evaluation harness:

- **Hand estimator.** Road-surface pixels in the bottom half of the render
  give the lane-center offset via their horizontal centroid; the nearest
  obstacle-valued pixel gives obstacle distance.
- **Learned estimator.** An MLP over the same 1024-pixel input, trained to
  regress both quantities, 40 epochs over 3,200 training frames.

Both are judged by MAE in meters against the simulator's true state — not
against each other, and not against a loss the model can minimize by
predicting the training mean.

## What we measured

```bash
cd 09-autonomous-driving/01-perception-baseline/core
python perception.py
```

| Quantity | Hand MAE | Learned MAE | Implication |
|---|---|---|---|
| Lateral offset | 0.588m | 0.072m | Learned recovers lane geometry from pixels; 8x better than the hand baseline |
| Obstacle distance | 0.469m | 6.526m | Learned is 14x WORSE — it fails at obstacle distance |

The obstacle result is the finding, not the lateral result. Obstacles occupy
an average of 0.8 pixels per frame (stage 00), so the training frames carry
almost no obstacle signal; a model that predicts the mean distance gets low
loss and high error. A render whose obstacles are this sparse cannot
support reactive obstacle avoidance by learning alone — the agentic stages
must either densify the render or rely on the state the render was built
from. This is a real, measured boundary, reported here before any policy is
blamed for it.

## The fix and its trade

The fix is measuring the information leak before any control runs: a hand
estimator as the honest baseline, a learned MLP as the challenger, both
judged by MAE against the simulator's true state — not against each other
and not against a loss a mean-predicting model can minimize. The trade is
that the metric is open-loop and the finding is asymmetric: the learned
estimator reads lateral offset 8x better than the hand baseline (0.072m
vs 0.588m), and obstacle distance 14x worse (6.526m vs 0.469m), because
the render's 0.8 obstacle pixels per frame carry almost no signal. The fix
buys correct attribution — a policy later blamed for failing avoidance
would be blamed for a boundary the render set — at the cost of an open-loop
number that can still disagree with closed-loop driving, which is exactly
what stages 03-04 exist to check.

## Who owns this loop

- **The perception owner** owns the two estimators and the MAE protocol;
  the learned estimator's obstacle-distance failure is reported here as a
  finding, not hidden until a policy crashes.
- **The render owner** owns the 0.8-pixel sparsity that drives the
  obstacle failure; densifying the render or leaning on simulator state
  are the two declared paths downstream can take.
- **The downstream policy owner** inherits the boundary: any controller
  that steers from this render must either densify it or use the state it
  was built from.

## Evidence boundary

MAE is an open-loop perception metric: it says nothing about whether a
controller using these estimates drives well. The closed-loop test is
stages 03-04's job, and it can disagree with open-loop perception — a model
that reads the lane perfectly can still drive off the road. Numbers trace
to [`runs/2026-08-07-perception.json`](runs/2026-08-07-perception.json).
