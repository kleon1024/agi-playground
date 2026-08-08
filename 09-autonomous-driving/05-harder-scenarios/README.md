---
status: verified
level: applied
base: none
verified: 2026-08-07
---

# Sharper curves, denser traffic — does the boundary hold or break?

**Goal:** evaluate the expert and the cloned policy on 50 out-of-distribution
scenarios whose generator settings are harder than any training scenario —
curvature amplitude raised from 0.3-0.7 to 0.9-1.4m, wavelength cut from
14-22 to 9-13m, obstacle count raised from 2-4 to 4-6.

**Why this stage exists.** A policy that drives only the distribution it was
trained on has not demonstrated driving — it has demonstrated interpolation.
The hard split is declared before the run and never tuned against: the
question is whether the in-distribution findings survive a shift, and the
answer is reported as a finding either way. This is the same discipline a
production eval holds itself to with held-out corridors, new geographies,
and logged-vs-live traffic.

## What you build

`core/hard_eval.py` — the stage-04 harness pointed at `sample_scenario(seed,
hard=True)` for seeds 200-249, running the expert and the stage-03 policy on
identical tracks.

## What we measured

```bash
cd 09-autonomous-driving/05-harder-scenarios/core
python hard_eval.py
```

| Policy | Completion | Collision | Off-road | Timeout | Mean x |
|---|---|---|---|---|---|
| Expert (hard) | 0.78 | 0.22 | 0.00 | 0.00 | 52.7 |
| Cloned (hard) | 0.04 | 0.24 | 0.00 | 0.72 | 12.2 |

The boundary breaks on both sides of the table. The expert loses ground —
its reactive planner cannot thread the denser obstacle fields — and the
cloned policy collapses: 0.04 completion and 0.72 timeout, with a mean
progress of 12m, barely past the first obstacles. The timeout rate, which
was zero in-distribution, is the signature of the compounding failure
amplified: on sharper curves the clone stalls against the first in-lane
obstacle instead of committing to a dodge.

## The fix and its trade

The fix is the hard split declared before the run and never tuned against:
curvature raised from 0.3-0.7 to 0.9-1.4m, wavelength cut from 14-22 to
9-13m, obstacle count raised from 2-4 to 4-6, on seeds 200-249 — the same
discipline a production eval holds itself to with held-out corridors and
new geographies. The trade is that the boundary breaks on both sides of
the table: the expert loses ground (0.92 to 0.78) because its reactive
planner cannot thread denser obstacle fields, and the clone collapses
(0.04 completion, 0.72 timeout, mean progress 12m). The shift is also
deliberately incomplete — obstacle speed is declared but not integrated,
since the collision check and render use static positions — so the boundary
measured here is a boundary of this generator, not of any real road
geometry.

## Who owns this loop

- **The scenario owner** owns the hard generator settings and seed range,
  frozen before the eval runs so the finding cannot be tuned away.
- **The eval owner** owns the identical-track protocol: expert and clone
  face the same 50 hard scenarios, so the collapse is comparative, not
  scenario-specific.
- **The report owner** owns the boundary-as-finding contract: the shift
  breaks on both sides and is reported as a result either way, never
  adjusted until the in-distribution claim is settled.

## Evidence boundary

The hard split shifts curvature, obstacle density, and declared obstacle
speed — the simulator's collision and render use static obstacle positions,
so speed is declared but not integrated (stage 00). The boundary measured
here is a boundary of this simulator's generator, not of any real road
geometry. Numbers trace to
[`runs/2026-08-07-hard.json`](runs/2026-08-07-hard.json).
