---
status: verified
level: applied
base: scratch
label: When the handoff crosses the band
verified: 2026-08-08
---

# The expert's four failures are not sandwiches

**Question:** stage 02 attributes its four lost scenarios (107, 108, 127,
142) to "obstacle sandwiches" — obstacles at both lane edges near an
in-lane obstacle, where no lateral offset is safe when the dodge lane
opens. That is an incident claim. Replay each failing scenario step by
step: is the attribution right, and if not, what is the real shared
mechanism and does fixing it close the gap?

**Before this:** [stage 02 — expert policy](../) and its 0.92/0.08 run.

## The attribution, tested

The run ([record](runs/2026-08-08-dodge-handoff.json)) applies the
stage-02 sandwich definition — an in-lane obstacle at offset 0 with
lane-edge obstacles at both +-1.2 within a longitudinal tolerance — to the
four failing scenarios, at 2m and at 3m tolerance. At both tolerances,
zero of the four scenarios is a sandwich. The attribution the stage writes
down is not what the scenarios contain.

## What the traces show instead

Every failing episode ends the same way: a lateral re-plan — the last
transition before the episode ends — crossing toward a target that clears
the obstacle at the target offset, while the crossing band clips it. The
four recorded decision traces:

| seed | end x | last transition | conflict at that step |
|---|---|---|---|
| 107 | 39.89 | step 69: −0.88 → +1.2 | dx −0.08, offset 0.0 |
| 108 | 25.76 | step 58: 0.30 → −1.2 | dx 0.85, offset 0.0 |
| 127 | 51.45 | step 102: −0.01 → −1.2 | dx 0.96, offset 0.0 |
| 142 | 20.16 | step 57: −0.58 → 0.0 | dx 0.54, offset −1.2 |

Seed 107 ends with the car crossing from −0.88 to +1.2 across an offset-0.0
obstacle already 0.08m behind the nose; 108 and 127 end with crossings from
near center to −1.2 while an offset-0.0 obstacle sits 0.85–0.96m ahead,
the crossing arc sweeping its band; 142 ends with a re-plan from −0.58 to
center while the −1.2 obstacle is 0.54m ahead and the car is still inside
its collision band.

The shared mechanism is the dodge-handoff transition. The expert re-plans a
lateral target from the kinematic safe set — the offsets that clear the
near obstacle group *at that offset* — but never checks that the path from
the current offset to the new one is feasible. Every one of the four
failures is a target that clears the obstacle and a crossing that does not.

## Where the failures live

The 50 eval scenarios split 32 clusters (two or more obstacles within 6m
longitudinally) against 18 non-clusters. All four fail seeds are in
clusters; none of the 18 non-cluster scenarios fails. The failures are not
uniform: they concentrate exactly where obstacle groups force lateral
re-plans, which is where the dodge-handoff transition fires most. An
attribution that named the shared mechanism would predict this
distribution; an attribution that named a rare configuration would not.

## The repair, measured

Two repairs, alone and combined:

- **Precise rear window**: an obstacle at or behind the car blocks a lane
  only when its exact centre distance is inside the collision radius; the
  base rear window is coarser.
- **Transition feasibility**: obstacles swept by the band between the
  current and target offset veto the crossing (hold and creep) or pace it.

| policy | completion | collision | fail seeds |
|---|---|---|---|
| base (stage 02) | 0.92 | 0.08 | 107, 108, 127, 142 |
| precise only | 0.94 | 0.06 | 107, 108, 127 |
| transition only | 0.90 | 0.10 | 108, 127, 133, 142, 144 |
| v7: precise + transition | 0.98 | 0.02 | 133 |

The decomposition is not additive in the naive sense. Precise alone fixes
142; transition alone fixes 107 but introduces 133 and 144; seeds 108 and
127 are fixed only by the conjunction — neither repair alone touches them.
The combined controller reaches 0.98 with one residual, and that residual
is not one of the four failures the stage attributed to sandwiches: it is
a failure the repair itself introduces.

## The residual: the guard's own hazard

Seed 133 — the base expert passes it; the combined repair collides at
x = 39.15. The guard's hold branch only fires while the conflict is beyond
8m (`conflict_dx > 8.0`); once the conflict is inside 8m the else branch
orders "cross fast" at 6.0 — the guard decides it is too late to hold and
commits to the crossing. In seed 133 the car is cutting from −1.0 to +1.2
while the in-lane obstacle at x=39.84 (offset 0.0, r 0.55) closes: the
recorded decision window shows the conflict dropping from dx 2.17 to 0.83
with two swept obstacles while the car crosses at 3–4.4 m/s, and the 3m
brake check slows it to 1.2 only after it is already inside the collision
radius (dx 0.83 against radius 0.90). The guard that was supposed to veto
infeasible crossings accelerates the car into one of its own.

## The fix-fix loop

The residual gets three follow-up variants of the guard, each measured in
the same run:

| variant | change | completion | collision | fail seeds |
|---|---|---|---|---|
| v7 (this detour) | hold if close swept + cur safe + conflict > 8m | 0.98 | 0.02 | 133 |
| v8 hold-when-safe | drop the 8m gate | 0.96 | 0.04 | 133, 144 |
| v9 hold-when-close | hold on any close swept obstacle | 0.88 | 0.12 | 108, 127, 133, 139, 142, 144 |
| v10 cross-slower | v7 rule, cross at 4.0 instead of 6.0 | 0.94 | 0.06 | 108, 127, 144 |

Each variant moves the failure to a different seed instead of removing it.
V8 fixes 133 but regresses 144, because "current offset safe" is false
exactly while the car is beside the swept obstacle — the hold releases at
the worst moment. V9 over-holds and stalls into the cluster, losing six
seeds. V10 fixes 133 but clips 144 on a knife-edge crossing that the 6.0 to
4.0 speed change alters by a few tenths of a meter. The pattern is the
industrial one: case mining, repair, new failure, residual. The transition
guard is necessary (0.92 to 0.98) but not sufficient — the residual queue
is tracked per seed, because a rate would hide that every obvious
parameterization trades one failure for another.

## The reading

The stage-02 "sandwich" attribution fails in the direction that matters
most for a post-mortem: it names a scenario *configuration* as the cause
when the shared mechanism is a *controller behavior* — re-planning without
transition feasibility — that any obstacle group can trigger. An
attribution to configuration tells the expert owner to wait for the
configuration; the measured repair shows the fix is in the controller, and
the cluster distribution shows the mechanism, not the configuration, is
what the failures share. The honest headline is 0.92 to 0.98 with a
recorded residual, not a clean 1.00.

## The fix and its trade

The fix is the two-part guard measured above: a precise rear window and a
transition-feasibility check, 0.92 to 0.98 with one residual. The trade:
the guard adds a stateful crossing decision whose own failure modes are now
the residual queue — the "cross fast" branch can accelerate into a swept
obstacle (133), and every follow-up parameterization found this session
regresses a different seed (recorded in the same run). The repair is a
controller change, not a
scenario change: it does not close the gap by editing the eval set, and the
stage's ceiling claim is now the repaired expert with its residual, not the
mis-attributed four.

## Who owns the loop

- **The expert owner** owns the dodge-handoff transition: every re-plan
  must check the crossing band, not just the target offset, and the
  residual queue (133 plus the exploration variants) lives with this
  owner, tracked per seed.
- **The eval owner** owns the attribution protocol: an incident claim must
  be tested against the scenario geometry before it becomes a stated
  failure mode, and the cluster/non-cluster split is the distribution an
  attribution must explain.
- **The mission owner** owns the ceiling claim: stage 04 compares the
  learner against the repaired expert (0.98, residual 133), so the
  imitation ceiling and the sandwich story are no longer the same number.

## Evidence boundary

One simulator's generator, 50 eval scenarios, a rule-based expert, and the
track's 0.1s discrete steering. The sandwich test is the stage's own
definition (an in-lane obstacle at 0 with both +-1.2 within 2m/3m); a
different attribution rule could find sandwiches elsewhere, but the four
decision traces and the residual decision window are recorded verbatim.
The exploration variants are recorded in the same run, not asserted from
memory. Numbers trace to
[`runs/2026-08-08-dodge-handoff.json`](runs/2026-08-08-dodge-handoff.json).

## Check your mental model

Answer each before opening it.

**1. Why is the sandwich attribution dangerous even though it sounds like
an explanation?**

<details>
<summary>Answer</summary>

Because it names a scenario configuration as the cause, and it is
falsifiable — the run falsifies it (zero of four at 2m and 3m). A
configuration attribution tells the expert owner to wait for the
configuration instead of fixing the controller, and it cannot explain the
distribution: the failures sit in obstacle clusters (4/4 in-cluster, 0/18
outside) because clusters force re-plans, not because sandwiches exist.
The traces show the mechanism is the dodge-handoff transition, which any
obstacle group can trigger.

</details>

**2. The combined repair loses seed 133, which the base passes. What does
0.92 → 0.98 mean when one of the losses is introduced by the repair
itself?**

<details>
<summary>Answer</summary>

It means the gain is real but not monotone: the guard's "cross fast"
branch can accelerate the car into a swept obstacle once the conflict is
inside 8m, which is exactly seed 133's mechanism. The honest headline is
0.98 with a recorded residual — a repair that moves the failure instead of
removing it is the normal state of an incident queue, and a claimed 1.00
would have hidden that the residual is a new failure mode, not a leftover.

</details>

**3. Three follow-up variants each regress a different seed. What does that
imply about tuning the guard further?**

<details>
<summary>Answer</summary>

That the residual is coupled to crossing geometry, not to one parameter:
holding more stalls into the cluster (v9), holding only when safe releases
beside the obstacle (v8), and crossing slower clips a knife-edge pass
(v10). No parameterization of the hold rule found in this run removes 133
without importing a different failure, which is why the queue is tracked
per seed rather than as a rate — a rate would average the rotation away.

</details>

## Next

Back to [stage 02](../). The detour lens now covers the whole first half of
the mission: the contract (margin) under
[stage 00](../../00-scenario-simulator/), the perception loop under
[stage 01](../../01-perception-baseline/), and the expert's own failures
here. Stage 03's cloned policy is the next place a claim is written
without a trace.
