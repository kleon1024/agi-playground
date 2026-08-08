---
status: verified
level: applied
base: scratch
label: When the nearest blob is the wrong thing to steer by
verified: 2026-08-08
---

# The blob could not see the pass

**Question:** stage 01 measures the render's information leak open-loop: the
hand estimator's obstacle-distance MAE is 0.469m and the learned estimator
fails at obstacle distance entirely. Those are per-frame numbers. What
happens when a controller actually steers from blob estimates in the loop —
does 0.4m of mean error become episodes lost, and where exactly?

**Before this:** [stage 01 — perception baseline](../) and its MAE runs.

## Steering from blobs, executed

The run ([record](runs/2026-08-08-blob-loop.json)) builds the blob estimator
a controller could actually use — connected components of obstacle-valued
pixels (v >= 2.0) in the 32x32 render, with distance from the nearest row,
lateral from the pixel centroid, and radius from the vertical extent — and
measures it two ways: open-loop against the oracle expert's true rollouts,
and closed-loop by re-targeting the oracle expert onto the blob beliefs on
the same 50 eval scenarios.

Blob visibility over the 7,432 oracle frames:

| frames with blobs | share | blob count distribution |
|---|---|---|
| 3,218 of 7,432 | 43.3% | 0: 4,119, 1: 2,597, 2: 634, 3+: 82 |

Blob estimate MAE by true distance, on the visible frames:

| true distance | n | distance MAE | lateral MAE |
|---|---|---|---|
| 0–2m | 909 | 0.359m | 0.085m |
| 2–4m | 795 | 0.417m | 0.099m |
| 4–6m | 744 | 0.436m | 0.109m |
| 6–8m | 770 | 0.413m | 0.105m |
| overall | 3,218 | 0.404m | 0.099m |

Closed-loop, the oracle expert on true state completes 0.92 of 50; the same
expert re-targeted onto the single nearest blob completes 0.90 and collides
on five episodes (104, 112, 133, 140, 142).

## The reading

The open-loop numbers look survivable: 0.40m distance error, 0.10m lateral,
smaller than the stage-01 hand baseline. The loop says otherwise — and the
failure set shows why. The belief planner does not simply drive worse; it
drives differently. It clears three of the oracle's four failures (107,
108, 127), shares one (142), and introduces four new collisions on episodes
the oracle clears (104, 112, 133, 140). The 0.02 completion gap is the
residue of a full rotation of the failure set, not a small perturbation of
the same failures.

The four mechanisms, from the recorded collision forensics:

- **The belief has no memory.** 56.7% of frames carry no blob at all — the
  8m render cutoff plus obstacles passing the car. The moment the blob
  vanishes, the belief scenario is empty and the oracle logic releases the
  dodge and returns to center at full throttle. The oracle on true state
  holds the dodge until the obstacle is 1.5m behind; the belief planner
  releases the moment its input disappears, while the true obstacle is
  still inside the collision band (the fatal frames show the passed
  obstacle at dx −0.82…−0.06).
- **Association flips.** The nearest blob is not a tracked object: in 4 of
  5 collision episodes the nearest-blob lateral jumps more than 1m between
  consecutive visible frames as the belief re-attaches to a different
  obstacle. Every re-attach is a re-plan from a wrong belief.
- **Meter-scale error at the deciding frame.** The blob distance is a
  single-row readout (0.25m per pixel), and at the frame that decides an
  episode the error is far above the 0.40m mean: seed 104's fatal frames
  believe the −1.2m obstacle is 1.38–1.88m away when it is 0.91–1.43m, so
  the governor's brake engages one reaction too late.
- **The nearest-blob shortcut ignores the window.** Seed 140 is a
  two-obstacle gate — both at ±1.2, dx 0.52–0.78, both in the decision
  window — and the single-blob planner commits to one side and clips the
  second. Seed 133 is a multi-obstacle interception where the cut-back
  crosses an incoming in-lane obstacle.

## The repairs, measured

Four planner-side repairs a stack might reach for, each on the same 50
scenarios:

| repair | completion | collision | fail seeds |
|---|---|---|---|
| belief (single nearest blob) | 0.90 | 0.10 | 104, 112, 133, 140, 142 |
| radius margin 0.35 → 0.68 | 0.84 | 0.16 | 103, 104, 112, 127, 130, 131, 140, 142 |
| cached track (last belief, 30 steps) | 0.90 | 0.10 | 104, 112, 133, 140, 142 |
| cautious governor (brake inside 4m) | 0.02 | 0.00 | 49 of 50 time out (seed 106 only) |
| feed every blob, not just the nearest | 0.98 | 0.02 | 144 |

Only the last one works, and it works for a reason the others cannot touch:

- The radius bump inflates a belief that already overestimates small
  obstacles (blob radius 0.62m for a ~0.5m obstacle) and adds false threats
  without touching the association and memory failures — it loses three
  episodes the single-blob planner cleared.
- The cached track only extends the life of the *nearest* belief. It
  changes nothing: identical fail set, because these five episodes are not
  lost to a vanishing blob that caching would revive.
- The cautious governor converts every pass through a visible obstacle zone
  into a stall: braking inside 4m parks the car, 49 of 50 scenarios time
  out. Conservatism at the wrong layer is itself a failure mode — the
  stage-05 stall lesson, imported early.
- Feeding every blob gives the safe-set logic the whole decision window:
  the second-threat failures (140), the re-attach misjudgments (104, 112,
  142), and the interception (133) all become visible to a planner that was
  built to consider every obstacle it is shown. The residual 144 is the
  knife-edge pass the margin detour under stage 00 already flagged.

The lesson is not "make the estimator more precise." The mean MAE is small
and getting it smaller does not appear in any of these repairs. The failure
is representation-level: no memory, no association, no window. The fix that
works changes what the policy is allowed to ignore, not a number.

This is the closed-loop lesson behind the closed-loop benchmark line in
the planning literature. nuPlan (Karnchanachari et al., 2024, arXiv
2403.04133) built a real-world closed-loop benchmark precisely because
open-loop planning accuracy does not predict closed-loop outcomes — the
same gap this detour measures as 0.40m open-loop MAE against five lost
episodes in the loop. The long-tail benchmark interPlan (Hallgarten et
al., 2024, arXiv 2404.07569) found that neither rule-based nor
learning-based planners navigate its rare configurations safely — the same
shape as the multi-obstacle gate (seed 140) and interception (seed 133)
that the standard scenario set never exposes. And CAR Planner (Kim and
Choi, 2025, TechRxiv) names the mechanism directly: imitation planners
suffer shortcut learning, latching onto a few spurious input channels, and
constraining the planner to use the whole evidence improves robustness —
the nearest-blob shortcut and the all-blobs repair are the same trade in
this render.

## The fix and its trade

The fix is the representation, not a parameter: the policy consumes every
detected blob (0.98 completion) and the perception contract declares what
a controller may ignore — nothing that rendered. The trade: the belief
still carries no memory and no association, so the residual knife-edge
passes (144) and the 8m visibility cutoff remain; the repair moves the
planner's blind spot from "second threat in the window" to "threat that
left the render," which is the smaller and better-scoped hole. The repair
does not densify the render or add tracking; it stops the policy from
throwing away the evidence it already has.

## Who owns the loop

- **The perception owner** owns the representation contract: a blob
  readout without memory or association is a decision input, not a sensor
  output, and its failure modes are the four above, not the MAE table.
- **The policy owner** owns the nearest-blob shortcut: the safe-set logic
  must be fed the full window or it will commit to one side of a gate.
- **The render owner** owns the 43.3% visibility and the 8m cutoff: the
  belief planner pays for the frames the render does not carry, and no
  planner-side repair can recover an obstacle that never rendered.

## Evidence boundary

One simulator's generator, 50 eval scenarios, one rule-based expert, and
the track's 0.1s discrete steering. The blob estimator is one choice
(connected components, nearest row); a denser render or a learned detector
would move the numbers, but the four mechanisms — memory, association,
deciding-frame error, window shortcut — are properties of any nearest-blob
representation this render supports. The fail sets are recorded verbatim;
external claims are dated and cited, never re-measured here. Numbers trace
to [`runs/2026-08-08-blob-loop.json`](runs/2026-08-08-blob-loop.json).

## Check your mental model

Answer each before opening it.

**1. The blob estimator's mean distance error (0.40m) is smaller than the
stage-01 hand baseline (0.469m). Why does it still lose episodes the
oracle clears?**

<details>
<summary>Answer</summary>

Because the mean is not the failure. The episodes are lost to
representation failures the MAE averages away: a vanished blob the planner
has no memory of, association flips that re-plan from a wrong belief, a
meter-scale error at the single frame that decides a pass, and a
nearest-only shortcut that never sees the second obstacle in the window.
An open-loop mean cannot predict a closed-loop rotation of the failure
set — this detour's 0.90/0.10 is the proof.

</details>

**2. The cautious governor — brake whenever a belief is inside 4m — is the
most conservative repair and it collapses completion to 0.02. Why?**

<details>
<summary>Answer</summary>

Because it converts every pass through a visible obstacle zone into a
stall: 49 of 50 scenarios time out and only seed 106 completes. The
governor cannot distinguish a pass from a threat without the same
representation the planner lacks, so conservatism at the wrong layer
replaces collisions with timeouts — which stage 05 shows is itself a
safety failure. A guard that cannot tell "dodge" from "wait" is not a
guard.

</details>

**3. Feeding every blob (0.98) fixes the gate episode 140, but the cached
track (0.90, identical fail set) changes nothing. What does that split
tell you about where the binding constraint is?**

<details>
<summary>Answer</summary>

That the constraint is the representation, not the estimator's lifetime.
The cache only extends the life of the single nearest belief; seed 140 is
lost because a second obstacle sits in the same decision window and the
nearest-only readout never surfaces it. Adding memory to a readout that
discards evidence cannot fix a failure caused by the discarding. The
all-blobs repair fixes 140 because it changes what the planner is shown,
not how long the showing lasts.

</details>

## Next

Back to [stage 01](../). The same detour lens moves to the expert: stage
02's writeup calls its four failures "obstacle sandwiches," and
[The expert's four failures are not sandwiches](../../02-expert-policy/when-the-handoff-crosses-the-band/)
replays those four scenarios step by step to test that attribution.
