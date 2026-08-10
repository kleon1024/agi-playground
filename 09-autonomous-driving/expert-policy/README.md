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
failure mode is the lesson: it loses four scenarios, and the attribution
for why is a stated claim, not a fact — replaying each failure step by step
shows the shared mechanism is the dodge-handoff transition, not the
"obstacle sandwich" this stage first wrote down. The re-measurement lives
under this stage, in
[The expert's four failures are not sandwiches](when-the-handoff-crosses-the-band/).

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
obstacle — and collides on the rest. The expert clears 46 of 50, losing
four to the dodge-handoff transition the detour under this stage traces.
The 0.64 completion gap between floor and expert is the room imitation
learning must recover; the expert's own 0.08 collision rate is the honest
boundary the learner cannot exceed.

## The fix and its trade

The fix is the ceiling-and-floor pair built from the same controller:
the expert (0.92 completion, 0.08 collision) is the ceiling imitation can
recover, and the lane-only version with the avoidance logic removed (0.28,
0.72) is the no-learning floor — the 0.64 gap is the room behavior cloning
must earn, isolated to exactly one variable. The trade is that the expert
sees true state, so it does not demonstrate that avoidance is learnable
from the render — stage 01 already showed the render barely carries
obstacle distance — and its own four handoff-transition failures are the
honest upper bound the learner cannot exceed; the detour under this stage
measures the repaired expert at 0.98 with one residual. The fix buys an
attribution target for stage 04's verdict at the cost of a ceiling that is
not a deployment candidate.

## Who owns this loop

- **The expert owner** owns the controller mechanisms (threat trigger,
  dodge selection, hold-until-passed, speed governor) and the
  dodge-handoff failure as a stated mode, not a hidden bug — the
  attribution itself is corrected under this stage.
- **The eval owner** owns the closed-loop protocol: the expert and floor
  run on the same 50 eval scenarios the learner will be judged on.
- **The mission owner** owns the floor/ceiling contract — the floor is the
  expert's controller minus avoidance, so stage 04's comparison isolates
  exactly what avoidance contributes.

## Evidence boundary

The expert sees true state, so it does not demonstrate that obstacle
avoidance is learnable from the render — stage 01 showed the render barely
carries obstacle distance. The expert is the ceiling, not a candidate
deployment. Numbers trace to
[`runs/2026-08-07-expert.json`](runs/2026-08-07-expert.json) and
[`runs/2026-08-07-lane-only.json`](runs/2026-08-07-lane-only.json).

## Next

The four failures this stage attributed to sandwiches are replayed step by
step in [The expert's four failures are not sandwiches](when-the-handoff-crosses-the-band/):
the attribution does not survive contact with the traces, the repaired
expert reaches 0.98 with one recorded residual, and stage 03's cloned
policy is next measured against the repaired ceiling.
