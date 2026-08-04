---
status: verified
level: applied
verified: 2026-07-31
label: Outcome report
---

# Did GRPO produce a policy worth deploying over either baseline?

**Before this:** [stage 01](../01-grpo/) trained 3 seeds of GRPO against the
grid-world and reported that every seed's greedy-decode policy collapses to
one constant, board-independent action, landing below the random baseline.

This stage holds that result against the contract
[`mission.yaml`](../mission.yaml) declared before stage 00 existed. It does
not get to soften the comparison after seeing the numbers.

## The contract, and the answer it produces

Mission 06's acceptance bar: beat both the random and greedy baselines by
more than GRPO's own seed-to-seed spread, or report an honest null result in
mission 01 04-rl's zero-gradient register. `core/report.py` reads stage 00's
`baselines.json` and stage 01's `grpo-seed{0,1,2}.json` directly and computes
this mechanically -- no numbers copied by hand.

```
random baseline:   0.2220
greedy baseline:   0.8240
GRPO (greedy decode): mean=0.0727  spread=0.0160  per_seed=[0.078, 0.062, 0.078]
GRPO (sampled decode, T=1.0): mean=0.1787  spread=0.0660  per_seed=[0.182, 0.144, 0.21]

greedy decode vs random:          margin -0.1493 -> decisively loses
greedy decode vs greedy baseline: margin -0.7513 -> decisively loses
sampled decode vs random:         margin -0.0433 -> within the noise band
sampled decode vs greedy baseline: margin -0.6453 -> decisively loses

VERDICT: NOT MET
```

`report.py`'s comparison rule: for a candidate mean `m` with per-seed spread
`s = max(per_seed) - min(per_seed)` and baseline `b`, margin is `m - b`. A
margin only counts as a real win or loss if `|margin| > s` -- otherwise it is
"within the noise band." Applied here: greedy-decode margin vs random is
`0.0727 - 0.222 = -0.1493`, and `0.1493 > 0.016` (the spread) -- a real,
decisive loss. Sampled-decode vs random is `0.1787 - 0.222 = -0.0433` against
a spread of `0.066` -- since `0.0433 < 0.066`, this is correctly reported as
"within the noise band" despite the negative point estimate.

<!-- interactive: SpreadVsMargin -->

Reporting an effect only when it exceeds measured run-to-run spread, rather
than any effect with the right sign, mirrors requiring statistical
significance before claiming a result in a small-sample experiment --
raw per-seed range rather than a computed variance-based interval, since a
formal confidence interval would be unreliable with only 3 seeds.

This is not mission 01's zero-gradient null result reused under a different
name: 199-200 of 200 steps per seed took a real gradient step, and the
policy clearly learned legal-move formatting and some board sensitivity
under sampled decode (peak 40-50% training-time success). But the policy a
deployed system would actually run -- greedy decode -- decisively loses to
both baselines, on every seed. `mission.yaml`'s acceptance bar names two
outcomes, beat-the-baselines or an honest null; this result is a third,
real thing -- non-degenerate training that still does not produce a useful
policy -- and it is reported as `NOT MET`, plainly, rather than stretched
into either named category.

## The failure catalogue

Acceptance also requires failures catalogued by category, not merely
counted:

```
degenerate rollout groups:            [0, 0, 1] / 200 steps per seed -- minor
board-independent policy collapse:    3/3 seeds -- each converges to one fixed action
non-stabilizing training-time success: 3/3 seeds -- peak 40-50%, falls to 12-19% by the end
```

The dominant failure mode is the second one, not the first: this run did not
fail the way mission 01's arithmetic run did (stuck at zero gradient). It
failed by learning a policy whose most-confident move at every position
stopped depending on the board at all -- a different, and more informative,
failure than never learning anything. Full mechanism and concrete completions
in stage 01's own
[`runs/2026-07-31-grpo-training.md`](../01-grpo/runs/2026-07-31-grpo-training.md).

## Compute

```
seed 0: 130.8s CPU, 200 steps
seed 1: 118.1s CPU, 200 steps
seed 2: 123.9s CPU, 200 steps
```

\$0 marginal cost -- local CPU lane only, no hosted-API spend, matching
`mission.yaml`'s `cost_budget`.

## Run it

```bash
cd missions/06-game-ai/02-report/core
uv run python report.py
```

`report.py` refuses to print a verdict if either upstream artifact is
missing -- it says `CANNOT DETERMINE` and names exactly which file is
absent, the same discipline missions 02's `09-report`, 03's `05-report`, and
05's `02-report` already established for this repository's report stages.

## What this does not establish

Whether more steps, more rollouts per group, a larger model, or a different
reward shape would let board-conditioning survive to greedy decode -- none
of those were varied. Nothing about a harder, real-time, or partially
observed game, per `mission.yaml`'s own `does_not_prove`.

## What a `NOT MET` verdict still established

Mission 06 set out to test the same reuse claim mission 05 tested for
vision: that mission 01's GRPO mechanism -- group-relative advantage,
clipped surrogate, KL leash -- transfers to a new reward source by changing
only the reward function and rollout environment. That claim held: stage 01
needed no changes to `rollout_group`, `grpo_loss`, or the training loop
itself, only a new reward function and a vocabulary built to match
`grpo.py`'s `PAD_ID`/`EOS_ID` convention. It also drew a sharper version of
the boundary mission 01's own null result first drew: escaping degenerate
rollout groups is necessary for GRPO to move a policy, but it is not
sufficient for the policy that results to be board-conditional under the
decode mode that matters. A `NOT MET` verdict on the deployment question does
not undo the reuse finding -- it says this particular training budget, on
this particular environment, produced a policy not worth deploying over
either baseline, which is a real, useful, and unflattering answer.
