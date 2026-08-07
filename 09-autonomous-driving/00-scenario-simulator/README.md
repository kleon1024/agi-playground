---
status: verified
level: applied
base: none
verified: 2026-08-07
---

# What makes a drive scoreable, and why generate it instead of scrap it?

**Goal:** a 2-D synthetic driving simulator whose episodes end in exactly one
of three outcomes — reach the target distance, collide, or drive off the
road — plus a procedural generator that creates train and eval tracks from
disjoint random seeds.

**Why this is stage 00 and not an appendix.** Every downstream number in this
topic is a completion rate over episodes. Before a single policy runs, the
episode itself has to be defined so precisely that two policies cannot
disagree about what happened, and the tracks have to be generated rather
than hand-placed so the eval split can be declared before any policy is
tuned. This stage builds the contract everything else is measured against.

## What you build

`core/driving_sim.py` — a deterministic 2-D world, CPU-cheap enough to roll
out an episode in milliseconds:

| Piece | What it is | Why it exists |
|---|---|---|
| Road | A sinusoidal lane center, 4m wide, `ROAD_HALF_WIDTH` from center | Lane-following with a curvature the car must actually track |
| Car | Position, heading, speed; `steer in {-1, 0, 1}` and `throttle in {0, 1}` at 10 Hz | The coarse action space is the point: a learned policy must map renders to these |
| Obstacles | Circles at lateral offsets `-1.2 / 0 / +1.2` from the lane center | Offsets matter: the car clears `+-1.2` by staying centered but must dodge `0`-offset obstacles |
| Render | 32x32 bird's-eye patch ahead of the car, ego heading up | The ONLY observation a learned policy sees; the expert sees true state |
| Outcome | Completed / collided / offroad, with steps and min clearance | One episode, one verdict — no ambiguity a later stage can argue with |

The obstacle schema declares a forward speed `vx`, and the generator samples
it, but the collision check and render use static positions. Speed-of-obstacle
motion is a declared next rung, not a silent omission: the claim under test
here is about imitation and closed-loop evaluation, and moving obstacles
would add a second variable before the first one is measured.

## What we measured

```bash
cd 09-autonomous-driving/00-scenario-simulator/core
python generate_scenarios.py
```

| Check | Value |
|---|---|
| Train scenarios | 100, seeds 0-99 |
| Eval scenarios | 50, seeds 100-149 |
| Eval render: road pixels / frame | 511.2 (of 1024) |
| Eval render: obstacle pixels / frame | 0.8 |
| Generation wall-clock | 0.002s |

The train/eval seed ranges are disjoint by construction and checked
programmatically — a policy that memorizes tracks rather than drives is
caught by the eval split. The obstacle-pixel figure is the first clue the
perception stage exploits: obstacles occupy under one pixel per frame on
average, which is why distance-to-obstacle is so hard to recover from the
render alone.

## Evidence boundary

This simulator is not a claim about driving. It is a scoreable environment
whose only purpose is to make the imitation-and-closed-loop method
measurable. Numbers here and in every later stage trace to runs in
[`runs/`](runs/), recorded with the exact command and seeds.
