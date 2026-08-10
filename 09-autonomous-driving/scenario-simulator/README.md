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

## The fix and its trade

The fix is the episode contract plus disjoint-seed generation: every
episode ends in exactly one of three outcomes, and the train (seeds 0-99)
and eval (seeds 100-149) ranges are disjoint by construction and checked
programmatically, so a policy that memorizes tracks is caught by the eval
split. The trade is that the determinism that makes everything scoreable —
two policies cannot disagree about what happened — is bought with a
declared omission: the obstacle schema carries a forward speed `vx`, but
the collision check and render use static positions, so moving obstacles
are a stated next rung, not a silent property. The 0.002s generation and
the 0.8 obstacle-pixel figure are the two numbers every later stage reads:
the first keeps the whole topic runnable on CPU, the second is the clue
that perception will have to confront.

## Who owns this loop

- **The simulator owner** owns the three-outcome episode contract and the
  disjoint seed ranges; no later completion rate exists without this
  definition.
- **The eval owner** inherits the split: every closed-loop number in
  stages 02-06 traces to the eval scenarios declared here, before any
  policy was tuned.
- **The render owner** owns the obstacle-pixel sparsity (0.8 of 1024 per
  frame) that stage 01 exploits and stage 04 pays for.

## Evidence boundary

This simulator is not a claim about driving. It is a scoreable environment
whose only purpose is to make the imitation-and-closed-loop method
measurable. Numbers here and in every later stage trace to runs in
[`runs/`](runs/), recorded with the exact command and seeds.

## Next

The episode contract fixes the collision margin at 0.35m. Whether that
number, not the policy, decides the completion rate is measured in
[The completion rate is a property of the contract, not the policy](when-the-margin-decides/),
and the same knife-edge lens carries into the perception stage:
[The blob could not see the pass](../01-perception-baseline/when-the-blob-lies/).
