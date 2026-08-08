---
status: verified
level: applied
base: scratch
label: When the budget splits
verified: 2026-08-07
---

# The privacy budget splits and dilutes every report

**Question:** [stage 40's privacy-safe attribution](../) budgets epsilon
as a shared resource. This chapter reads the executed split and asks
what every extra report costs.

**Before this:** [stage 40 — privacy-safe attribution](../) and its
executed DP-noise model.

## The split, executed

The run ([record](runs/2026-08-07-budget-splits-read.md)) divides a
total epsilon of 2.0 across different numbers of reports:

| reports | epsilon each | noise scale |
|---|---:|---:|
| 1 | 2.000 | 0.5 |
| 10 | 0.200 | 5.0 |
| 100 | 0.020 | 50.0 |

## The reading

One report gets epsilon 2.0 and noise scale 0.5; 100 reports get
epsilon 0.02 each and noise scale 50. The privacy budget is a shared
resource — every additional report dilutes the signal of all the
others. Publishing more analyses is not free: each one consumes epsilon,
and the noise each report must carry grows in proportion. The
attribution team's appetite for reports and the accuracy of each report
are the same decision, made once at the budget level.

## The fix and its trade

The fix is sequential-composition accounting: track every epsilon
spend in a privacy ledger (a DP accountant), so the team sees the
remaining budget the way it sees a spend budget, and plan the report
schedule against the total instead of approving reports one at a time.
The additive composition theorem makes the split exactly zero-sum —
each report's epsilon consumes a share that every other report loses
(Dwork 2006, ICALP; Delaney et al., "Differentially Private Ad
Conversion Measurement", to appear PoPETs 2024, arXiv:2403.15224,
which measures the ad-measurement analogue of the same trade). The
trade is that accounting only prices the dilution, it does not stop
it: the alternative is to stop publishing fine-grained per-report
counts and move to a central aggregator or a trusted execution
environment that computes the statistics once on raw data and adds a
single round of noise, which trades per-report privacy against the
operational cost and trust model of a central server — the two ends
of the privacy-budget spectrum the stage's budget decision has to pick
between.

## Who owns the loop

- **The measurement and privacy team** owns the epsilon ledger: a DP
  accountant that tracks every report's spend so the remaining budget is
  visible the way a spend budget is.
- **The reporting team** owns the report schedule against the total —
  approving reports one at a time is how a shared resource gets
  silently diluted.
- **The product and trust team** owns the central-aggregator
  alternative that trades per-report privacy for the operational cost
  and trust model of a central server.

## Evidence boundary

The executed split over three declared report counts (illustrative,
deterministic, assumed sequential composition). It demonstrates the
mechanism; real budget management needs the composition theorem and the
actual report schedule, which a privacy accounting system tracks.

## Check your mental model

Answer each before opening it.

**1. Why does one extra report make every other report noisier?**

<details>
<summary>Answer</summary>

Because the total epsilon is fixed. Each report consumes a share, so
adding a report shrinks every existing share — the executed split drops
epsilon from 2.0 at one report to 0.02 at 100, raising the noise scale
from 0.5 to 50. The budget is a resource the whole team spends, and
spending is zero-sum across reports.

</details>

**2. What decision does this force on the attribution team?**

<details>
<summary>Answer</summary>

How many reports the budget can afford. More reports means more
attribution views and weaker signal in each; fewer reports means
stronger signal and fewer views. The trade is decided once at the
budget level, not per report — which is exactly why epsilon accounting
exists. The noise-too-high detour shows the consequence when the split
pushes the signal past the collapse point.

</details>

## Next

Back to [stage 40](../). The
[noise-too-high detour](../when-the-noise-is-too-high/) shows the
collapse point that sets how far the budget can be split.
