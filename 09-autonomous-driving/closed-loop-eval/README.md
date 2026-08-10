---
status: verified
level: applied
base: none
verified: 2026-08-07
---

# Does the cloned policy drive, and where does it fall short?

**Goal:** run the stage-03 policy in the loop on the same 50 eval scenarios
as the expert, and report its completion rate beside the floor and the
ceiling — with the stage-03 imitation accuracy beside it, on purpose.

**Why this stage exists.** This is the stage the topic is named for. Stage 03
measured what the policy knows; here the policy's own actions move the car,
and every error changes the next render. If small action errors compound,
the car drifts into states the expert never visited, and the policy's
imitation accuracy stops predicting its driving quality. Reporting the two
numbers side by side is not optional decoration — it is the finding.

## What you build

`core/eval_loop.py` — three closed-loop evals over identical scenarios:
the lane-only floor, the expert, and the cloned policy, each rolling out up
to 400 steps per scenario and classifying every episode into one of the
stage-00 outcome classes.

## What we measured

```bash
cd 09-autonomous-driving/04-closed-loop-eval/core
python eval_loop.py
```

| Policy | Completion | Collision | Off-road | Mean x |
|---|---|---|---|---|
| Lane-only floor | 0.28 | 0.72 | 0.00 | 35.2 |
| Expert | 0.92 | 0.08 | 0.00 | 58.2 |
| Cloned | 0.28 | 0.72 | 0.00 | 35.2 |

**The gap:** 0.77 joint imitation accuracy (stage 03) collapses to 0.28
in-loop completion — statistically indistinguishable from the no-learning
floor. The cloned policy reproduces the expert's dominant actions (steer
straight, accelerate), matches it on 77% of frames, and in the loop it
behaves exactly like the controller with avoidance removed. This is
compounding error plus action imbalance in one number: the dodge frames the
model got wrong were the only frames that mattered, and each missed dodge
put the car somewhere the next frame's prediction was also wrong.

The verdict against the declared acceptance criterion is **NOT MET** —
vanilla behavior cloning did not beat the rule baseline. That is the
measured result, reported rather than tuned away; the declared next rung is
weighted/labeled losses that rebalance the dodge frames, then DAgger-style
on-policy querying, neither of which this topic runs.

## The fix and its trade

The fix is the in-loop evaluation itself: the stage-03 policy runs on the
same 50 eval scenarios as the floor and the ceiling, and its imitation
accuracy is reported beside its completion rate on purpose. The trade is
the headline it produces: 0.77 joint imitation accuracy collapses to 0.28
in-loop completion — statistically indistinguishable from the no-learning
floor, whose numbers it exactly matches (0.28, 0.72, mean x 35.2). The
verdict against the declared acceptance criterion is NOT MET, reported
rather than tuned away. The fix buys the topic's central finding —
compounding error and action imbalance compressed into one number — at the
cost of a negative headline that the declared contract requires.

## Who owns this loop

- **The eval owner** owns the identical-scenario harness and the
  three-outcome classification; the floor, ceiling, and learner run the
  same episodes, so the comparison isolates the policy, not the track.
- **The model owner** owns the stage-03 artifact: the same weights are
  evaluated in the loop with no retraining, which is what makes the
  0.77-to-0.28 gap a property of the method, not of a fresh model.
- **The mission owner** owns the acceptance criterion and the declared
  next rung (weighted/labeled losses, then DAgger-style on-policy
  querying) — named here, run in a later topic if at all.

## Evidence boundary

This failure is specific to this simulator's render sparsity (stage 01)
and this expert's action distribution — it is evidence about the method's
failure mode, not about every behavior-cloning system. Numbers trace to
[`runs/2026-08-07-closed-loop.json`](runs/2026-08-07-closed-loop.json).

## Next

The 0.77-to-0.28 gap is opened further in
[when the open-loop score lies](when-the-open-loop-lies/): where the
imitation error actually lives (per-action class), how early the clone's
trajectory leaves the expert's, and why the expert disagrees with the
learner on 59% of the states the learner drives. The same policy is then
run out of distribution in
[stage 05 — harder scenarios](../05-harder-scenarios/).
