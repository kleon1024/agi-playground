---
status: verified
level: applied
base: none
verified: 2026-08-07
---

# What does a rule-based expert actually achieve in the loop?

**Goal:** a lane-following controller with reactive obstacle avoidance,
evaluated closed-loop on the 50 eval scenarios, plus the same controller
with the avoidance logic removed as the no-learning floor.

**Why this stage exists.** The expert is the ceiling of what behavior
cloning can recover — the learner's demonstrations come from it, so the
learner cannot exceed it. The expert also fixes the baseline contract: the
floor is the same controller minus its avoidance logic, so the comparison in
stage 04 isolates exactly what avoidance contributes. Before this stage, no
number exists for either bound, and a cloned policy's failure cannot be
attributed.

## What you build

`core/expert.py` — a reactive planner that sees the true simulator state
(the learner never does):

| Mechanism | What it does |
|---|---|
| Lane keeping | Steer toward the lane center at a lookahead point, accelerate |
| Threat trigger | The nearest obstacle the current lateral offset does NOT clear, found before it is the nearest obstacle — waiting for that fires too late |
| Dodge selection | Closest lateral offset from `{0, +-1.2, +-1.55}` that clears the near obstacle group, re-planned every step |
| Hold-until-passed | Keep the dodge offset until the triggering obstacle is 1.5m behind — returning on "barely safe" steps makes the margin check flip-flop and turns clean passes into collisions |
| Speed governor | Creep toward obstacle zones (discrete steering can only hold an offset at low speed), accelerate in clear stretches |

The controller is deliberately simple enough to read in one sitting. Its
failure mode is the lesson: the four scenarios it cannot pass are "obstacle
sandwiches" — obstacles at both lane edges within ~2m of an in-lane
obstacle, where no lateral offset is safe at the moment the dodge lane opens.

## What we measured

```bash
cd 09-autonomous-driving/02-expert-policy/core
python expert.py
```

| Policy | Completion | Collision | Off-road | Mean steps |
|---|---|---|---|---|
| Lane-only floor | 0.28 | 0.72 | 0.00 | 76.2 |
| Expert | 0.92 | 0.08 | 0.00 | 148.6 |

The floor completes 14 of 50 scenarios — exactly the ones with no in-lane
obstacle — and collides on the rest. The expert clears 46 of 50, losing four
to the sandwich configuration above. The 0.64 completion gap between floor
and expert is the room imitation learning must recover; the expert's own
0.08 collision rate is the honest boundary the learner cannot exceed.

## Evidence boundary

The expert sees true state, so it does not demonstrate that obstacle
avoidance is learnable from the render — stage 01 showed the render barely
carries obstacle distance. The expert is the ceiling, not a candidate
deployment. Numbers trace to
[`runs/2026-08-07-expert.json`](runs/2026-08-07-expert.json) and
[`runs/2026-08-07-lane-only.json`](runs/2026-08-07-lane-only.json).
