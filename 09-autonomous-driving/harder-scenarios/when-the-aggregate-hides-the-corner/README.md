---
status: verified
level: applied
base: scratch
label: When the aggregate hides the corner
verified: 2026-08-08
---

# The aggregate boundary hides a cliff the ODD cells do not share

**Question:** stage 05 reports one clone row — 0.04 completion, 0.24
collision, 0.72 timeout. Does that boundary hold uniformly across the hard
operational design domain, or does it live in a cell?

**Before this:** [stage 05 — harder scenarios](../) and its hard-split run.

## The cells, executed

The run ([record](runs/2026-08-08-odd-coverage.json)) splits the same 50
hard scenarios into thirds of the declared curvature range (amplitude
[0.9, 1.4]) and reports each cell for the clone and the expert.

| amplitude cell | n | clone complete | clone collision | clone timeout | expert complete |
|---|---|---|---|---|---|
| [0.90, 1.07) | 15 | 0.067 | 0.533 | 0.400 | 0.733 |
| [1.07, 1.23) | 16 | 0.062 | 0.250 | 0.688 | 0.812 |
| [1.23, 1.40) | 19 | 0.000 | 0.000 | 1.000 | 0.789 |

## The reading

The aggregate flattens a cliff. The clone's completion falls 0.067, 0.062,
0.000 across the cells and — more telling — the failure mode itself shifts:
collision-dominated in the mild cell (0.533), timeout-dominated in the
extreme cell (1.000). The two completions behind the 0.04 aggregate both
sit in the two mildest cells. The expert, by contrast, is flat: 0.73-0.81
completion in every cell, because its degradation is a mild collision rate,
not a stall cliff. The 0.04 row is true and misleading at once — true as
an average, misleading as a claim about the ODD, whose extreme third the
policy cannot enter at all.

The second half of the run prices the coverage. The extreme cell's 0.000
completion rests on n = 19, whose 95% upper bound is 0.176 — the data
cannot distinguish "never" from "17%". Bounding the rate at 0.05 would need
72 scenarios per cell, 216 total; at this simulator's measured 0.11 s per
hard scenario that is about 24 s of wall-clock. The constraint is sample
design, not budget: production autonomy samples scenario databases per
declared ODD cell (nuPlan's scenario taxonomy is one instance) and reports
per-cell rates, because the same n-per-cell math holds when each scenario
costs real hours in a high-fidelity simulator.

This is the same failure family as the recommendation side's
[aggregate AUC lying about dense slices](../../../02-personalized-discovery/recommendation/65-sparse-labels/when-the-aggregate-auc-lies/):
an aggregate metric reads as one number and hides the slices that decide
whether the system works. The confidence-interval mechanics behind the
coverage numbers are walked in the mission-01
[why-believe-the-number](../../../01-language-model/07-eval/why-believe-the-number/)
chapter; here they are applied to an eval cell.

## The fix and its trade

The fix is to report the boundary per declared ODD cell and sample the
cells deliberately: stratify the scenario draw by the declared ranges
instead of drawing uniformly and aggregating. The trade is that per-cell
reporting is more work and more uncomfortable — it replaces one number with
a table, it forces the team to declare the ODD cells up front (before the
run, or the cells can be tuned to fit the result), and it multiplies the
sample budget by the number of cells. The measured cost here — 216
scenarios, about 24 s — shows the budget is not the obstacle in this
simulator; in a real one, per-cell targets are exactly why scenario
libraries exist.

## Who owns the loop

- **The scenario owner** owns the declared ODD cells and the stratified
  draw: the cells are frozen before the eval runs, the same discipline
  stage 05 applies to the hard split itself.
- **The eval owner** owns the per-cell report and the n it rests on: a
  completion rate with no cell breakdown and no cell n is a claim about an
  average the ODD does not have.
- **The safety and metrics team** owns what the corner verdict means
  operationally: a 0.000 in the extreme cell is a boundary of the policy,
  and the coverage math decides how much evidence that boundary has.

## Evidence boundary

Cells are thirds of the declared amplitude range only; wavelength, obstacle
count, and declared speed are not sliced here, and declared speeds are not
integrated by the simulator (stage 00). The mixed-cell intervals use the
Wilson approximation; the zero-success cell uses the exact Clopper-Pearson
bound. Numbers trace to
[`runs/2026-08-08-odd-coverage.json`](runs/2026-08-08-odd-coverage.json).

## Check your mental model

Answer each before opening it.

**1. How can a 0.04 completion rate be true and misleading at the same
time?**

<details>
<summary>Answer</summary>

It is the true average over 50 scenarios, and it is misleading about the
ODD because the average hides a cliff: the clone completes 6-7% of the mild
cells and 0% of the extreme third, where every episode times out. Two
things describe the system better than the aggregate — the per-cell
completion rates, and the failure-mode shift from collision to stall. The
aggregate compresses both away.

</details>

**2. What does n = 19 actually allow you to claim about the extreme cell?**

<details>
<summary>Answer</summary>

That the clone completed zero of nineteen — with a 95% upper bound of
0.176. You can claim the rate is low, not that it is zero: the sample
cannot distinguish a true 0% from a true 17%. To bound the rate at 5% you
would need 72 scenarios in that cell, and the measured cost of getting
them is about 24 s in this simulator — which is why a thin corner cell is
a sampling decision, not a budget constraint.

</details>

## Next

Back to [stage 05](../). The
[stall detour](../when-the-policy-stalls/) shows what the extreme cell's
1.000 timeout is made of.
