---
status: verified
level: applied
base: scratch
label: When the policy stalls
verified: 2026-08-08
---

# A timeout is the policy never deciding

**Question:** stage 05's hard split ends 72% of the clone's episodes in
timeout with a mean progress of 12 m. What is a timeout made of — how far
does the car get, how fast, and why is an episode with no collision still a
safety failure?

**Before this:** [stage 05 — harder scenarios](../) and its hard-split run.

## The stall, executed

The run ([record](runs/2026-08-08-stall-profile.json)) profiles every hard
episode for the clone and the expert: progress, speed, and whether the car
is still moving forward at the end.

Clone, timed-out episodes only (36 of 50):

| quantity | value |
|---|---|
| mean progress | 3.6 m |
| mean share of steps spent below 0.5 m/s | 0.968 |
| episodes with under 1 m of progress in the final 50 steps | 100% |
| mean speed at episode end | 0.0 m/s |
| obstacles passed | 0 |

Median progress across all 50 clone episodes is 3.6 m and 76% end before
x = 15. The expert on the same tracks never times out: 0.78 completion,
0.22 collision, and 0.023 of its time below 0.5 m/s.

## The reading

A timeout is not "nothing happened" — it is the policy braking to a
standstill in front of the first obstacle and never committing to a pass.
The timed-out episodes creep for 97% of their steps, end stopped, and have
passed zero obstacles. Compare the failure modes: the expert's errors are
collisions — a maneuver committed and wrong; the clone's errors are stalls —
no maneuver committed at all. The stage-05 collision rate (0.24) understates
the failure because most of the damage is the stall.

Production autonomy treats this as a first-class failure, not a neutral
outcome. SAE J3016 defines competence as conditional on the operational
design domain; when the ODD lapses, UNECE R157 requires an automated
lane-keeping system to perform a minimal risk maneuver — slow down and stop
in lane — not to keep driving and not to simply stop deciding. A planner
that times out has no fallback, and a closed-loop benchmark like nuPlan
scores reaching the goal, so a stalled episode is a failure with no crash
required. The stall is the eval's way of saying the policy has no answer
for this state.

## The fix and its trade

The fix is a fallback layer with a no-progress trigger: detect that the
policy has stopped making forward progress and hand the episode to a
declared safe-state maneuver — here, a rule governor that brakes to a stop
in lane; on a real stack, the minimal risk maneuver. The trade is that the
trigger is a policy decision: trigger too early and the fallback seizes
control in situations the learner could still solve — it becomes the
lane-only floor, which this mission measures at 0.28 completion; trigger
too late and the stall becomes a collision. A second fix targets the cause
rather than the symptom: on-policy training (DAGGER-style, as the
[open-loop-lies detour](../../04-closed-loop-eval/when-the-open-loop-lies/) walks) that labels the
stall states, so the learner sees what the expert does at the obstacle it
refuses to pass.

## Who owns the loop

- **The safety and fallback owner** owns the no-progress trigger and the
  safe-state maneuver it hands to — the MRM analog, and the threshold that
  decides when the learner is out of its depth.
- **The policy owner** owns why the learner stalls: the brake class it
  learned at 0.33 accuracy is the same class that produces the 97% creep
  here.
- **The eval owner** owns reporting timeout beside completion and
  collision, and classifying the stall as a failure mode rather than a
  neutral outcome.

## Evidence boundary

The stall profile is measured on this simulator's hard generator (static
obstacle positions; declared speeds not integrated) and this clone. A real
automated lane-keeping system must reach a safe state under R157's
definition, which no toy-simulator result claims to measure. Numbers trace
to [`runs/2026-08-08-stall-profile.json`](runs/2026-08-08-stall-profile.json).

## Check your mental model

Answer each before opening it.

**1. Why is a timeout a different failure signal from a collision here?**

<details>
<summary>Answer</summary>

A collision is a wrong decision made decisively; a timeout is no decision
at all. The expert's failures are collisions (0.22 on hard scenarios) — its
controller committed to a maneuver and lost. The clone's failures are
stalls: 97% of the episode below 0.5 m/s, stopped at the first obstacle,
zero obstacles passed. Safety regulation (UNECE R157) requires the system
to reach a declared safe state when the situation lapses; a policy that
neither passes nor stops on purpose has no fallback, and the timeout rate
is how the eval counts that.

</details>

**2. What would change if the eval only reported completion and collision?**

<details>
<summary>Answer</summary>

The 0.72 timeout would vanish from the report. The clone's hard result
would read 0.04 completion and 0.24 collision, and the dominant failure —
36 episodes that stopped moving and never decided — would be invisible.
The timeout column is what makes the stall a finding instead of an
unclassified remainder.

</details>

## Next

Back to [stage 05](../). The
[aggregate-boundary detour](../when-the-aggregate-hides-the-corner/) shows
where those stalls live in the declared ODD and how much a 50-scenario
draw can say about them.
