---
status: verified
level: applied
base: scratch
label: When the collision margin decides the verdict
verified: 2026-08-08
---

# The completion rate is a property of the contract, not the policy

**Question:** stage 00's episode contract fixes the collision margin at
0.35m and the finish line at 60m. Stage 02 reports 0.92 completion on that
contract. Which knob in the contract actually decides the verdict — the
margin, the finish line, or the policy?

**Before this:** [stage 00 — scenario simulator](../) and its contract.

## Which knob moves the rate, executed

The run ([record](runs/2026-08-08-margin-sweep.json)) sweeps the collision
margin from 0.20 to 0.50m and the finish line from 55 to 65m on the same
50 eval scenarios, for both the expert and the lane-only floor.

Expert completion by collision margin:

| margin (m) | completion | collision | new failures vs 0.35m |
|---|---|---|---|
| 0.20 | 0.96 | 0.04 | none; 107 and 142 pass |
| 0.30 | 0.92 | 0.08 | same as 0.35 (107, 108, 127, 142) |
| 0.35 (standard) | 0.92 | 0.08 | baseline |
| 0.40 | 0.92 | 0.08 | same as 0.35 |
| 0.50 | 0.86 | 0.14 | +120, 129, 144 |

Finish-line sweep at the standard margin: 0.92 at 55, 60, and 65m —
inert, same four fail seeds.

Floor completion by collision margin: 0.28 at 0.20–0.40, 0.26 at 0.50 —
flat, because the floor collides deep (it never dodges) and the margin
only reclassifies episodes that were already near the boundary.

## The reading

The expert's failures are marginal. Its four standard failures live in a
collision band of roughly 0.10–0.14m of slack: at margin 0.20 two of them
(107, 142) clear, at 0.50 three more (120, 129, 144) join them. The sweep
over the same 46 completed episodes shows why: 17 of 46 completions carry
less than 0.25m of margin slack at the tightest pass (minimum 0.09m,
median 0.287m). A ±15% change in the contract reclassifies episodes whose
true separation from the obstacle is inside the margin itself.

The floor's 0.28 is insensitive because its collisions are deep, not
marginal — removing avoidance logic loses every in-lane obstacle episode
regardless of how the boundary is drawn. The floor flat line and the
expert's swing line are the same lesson from two directions: the
completion number on a contract page is a statement about the margin, the
finish line, and the generator, and only weakly about the policy. Anyone
comparing two autonomous-driving claims must first ask which margin each
was measured under.

This is the mechanism behind the published safety-claim spread. The
safety-impact analyses published with the Waymo Safety Data Hub
(Scanlon and Kusano, 2024) and the tolerance-based event-threshold work
(Campolettano, Scanlon, McMurry, Kusano, and Victor, 2025, Traffic
Injury Prevention) show crash-surrogate outcomes shifting with the
interaction model and the proximity threshold used to declare an event:
the metric is a policy of the reporting pipeline before it is a fact
about the vehicle. IIHS (2026-07) makes the same point for comparability:
its Waymo crash-rate study had to discard roughly a quarter of reported
crashes as duplicates, off-public-road, or not true crashes, so the
verdict depends on how an event is defined before it depends on the
fleet.

## The fix and its trade

The fix is to stop quoting a single completion number and to declare the
contract as a vector: margin, finish line, generator, and the slack
distribution over the completed set. The trade is that a slack
distribution is less legible than a rate, and once the margin is declared
small the honest headline gets worse — the same expert is 0.96 at 0.20m
and 0.86 at 0.50m, and neither number is "the" expert. The repair does
not make the policy safer; it stops the number from overstating how
safe the policy is.

## Who owns the loop

- **The eval owner** owns the contract vector: a completion rate without
  the margin, finish line, and slack distribution is not comparable.
- **The safety owner** owns the margin itself: choosing 0.35m is a
  safety decision with a measurable effect on the headline, and the
  slack histogram is the evidence the decision is made on.
- **The mission owner** owns the floor comparison: the flat 0.28 floor
  is the control that keeps the expert's swing from being read as
  policy quality.

## Evidence boundary

One simulator's generator, 50 scenarios, one rule-based expert, and the
track's 0.1s discrete steering. The margins are swept in 0.1m steps and
the finish line in 5m steps; the exact swing (0.96 to 0.86) is specific
to this track, but the mechanism — failures inside the margin band —
is the property any re-measurement of this simulator reproduces.
External claims are dated and cited, never re-measured here. Numbers
trace to [`runs/2026-08-08-margin-sweep.json`](runs/2026-08-08-margin-sweep.json).

## Check your mental model

Answer each before opening it.

**1. Why does the floor's completion stay flat at 0.28 while the expert
swings 0.96 to 0.86?**

<details>
<summary>Answer</summary>

Because the floor never dodges: its collisions are deep passes through
in-lane obstacles, and a collision is a collision at any margin. The
expert clears obstacles with as little as 0.09m of slack, so its verdicts
live inside the margin band and reclassify when the band is resized.
Flatness means the failures are not boundary cases; swing means they are.

</details>

**2. If two papers report 0.94 and 0.90 completion on "the same
task", what must you check before comparing?**

<details>
<summary>Answer</summary>

The collision margin and the finish line first: this run shows 0.20m vs
0.50m flips the expert's own rate by 0.10 with no code change, and the
flip seeds (107, 120, 129, 142, 144) are a different failure set at each
end. Without the contract vector, the 0.04 gap between the two papers
is indistinguishable from measurement noise under different margins.

</details>

## Next

Back to [stage 00](../). The same marginal-failure lens applies to the
perception stage: [when the blob could not see the pass](../../01-perception-baseline/when-the-blob-lies/)
shows a policy steering from blob estimates losing episodes to the same
kind of knife-edge passes, and
[The expert's four failures are not sandwiches](../../02-expert-policy/when-the-handoff-crosses-the-band/)
shows the expert's four failures are not what its own writeup claims.
