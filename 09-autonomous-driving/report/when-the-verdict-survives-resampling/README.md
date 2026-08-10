---
status: verified
level: applied
base: scratch
label: When the verdict survives resampling
verified: 2026-08-08
---

# The 0.28-vs-0.28 verdict is the same 14 scenarios twice

**Question:** stage 06's NOT-MET verdict — cloned 0.28 vs rule baseline
0.28 — is a point estimate on one 50-scenario sample. How much does the
verdict depend on which 50 scenarios were drawn, and are the two 0.28 cells
the same scenarios or different ones?

**Before this:** [stage 06 — report](../) and its reading-only run.

## The verdict under resampling, executed

The run ([record](runs/2026-08-08-verdict-bootstrap.json)) re-simulates
every cell per seed — clone, lane-only floor, and expert on eval seeds
100–149; hard clone and hard expert on hard seeds 200–249 — then draws
2,000 paired bootstrap samples of 50 seeds with replacement. Pairing keeps
the per-seed correlation between policies: each draw compares clone and
floor on the same scenarios.

The per-seed outcome distribution reproduces the stage-06 table exactly:

| cell | completed | collided | timeout |
|---|---:|---:|---:|
| clone (in-distribution) | 14 | 36 | 0 |
| rule baseline (in-distribution) | 14 | 36 | 0 |
| expert (in-distribution) | 46 | 4 | 0 |
| clone (hard) | 2 | 12 | 36 |
| expert (hard) | 39 | 11 | 0 |

The bootstrap, as a distribution over the 50-seed draw:

| comparison | mean difference | 95% CI | P(diff > 0) |
|---|---:|---:|---:|
| clone minus floor | 0.0 | [0.00, 0.00] | 0.0 |
| expert minus clone | 0.641 | [0.50, 0.78] | 1.0 |
| hard expert minus hard clone | 0.739 | [0.60, 0.86] | 1.0 |

And the per-seed relation between the two policies that tie at 0.28:

| quantity | value |
|---|---:|
| shared winners (clone and floor both complete) | 14 of 14 |
| clone-only winners | 0 |
| floor-only winners | 0 |
| winner-set IoU | 1.0 |
| scenarios the clone completes that the floor fails | 0 |

## The reading

The verdict is robust — but for a reason the rate table hides. The clone
and the floor complete exactly the same 14 scenarios and fail exactly the
same 36: the winner sets are identical (IoU 1.0), so no 50-seed draw can
show the clone above the floor, and P(clone > floor) is 0.0 with a
zero-width CI. The NOT-MET verdict is not fragile to sampling — it is
robust because the clone's competence is a strict subset of the floor's.
The clone adds nothing over a controller with no avoidance logic on this
sample, which is why the two rates agree on every seed, not just in
aggregate.

The MET rows are also robust, but their size is the uncertain part: expert
beats clone on every draw, 95% CI [0.50, 0.78]; hard expert beats hard
clone on every draw, CI [0.60, 0.86]. The report's least-certain numbers
are its conclusions that pass — the gap is reliably positive, its width is
not. On the hard split the clone's 36 timeouts are the same no-decision
failure the [policy-stalls detour](../../05-harder-scenarios/when-the-policy-stalls/)
profiles.

This is the industrial point. Two rate cells that look like a near-tie can
be two different worlds, and the aggregate cannot tell them apart: here the
0.28-vs-0.28 is total order containment, so a blend of the two policies
clears nothing; in the other world — close rates on disjoint winner sets —
the same table would hide complementarity, and keeping both policies would
clear the bar. The per-seed winner set is the one-line check that says
which world a verdict lives in, and the bootstrap (Efron 1979) turns the
point estimate into an interval the way online-experiment practice
(Kohavi, Tang, and Xu 2020) refuses to ship a treatment effect without one —
a single-sample verdict, like a single-seed RL result (Henderson et al.
2018), is a claim without a variance.

## The fix and its trade

The fix is to report per-seed outcome sets beside the rate cells: the
report's verdicts stay, but each comparison row gains its winner-set IoU
and a bootstrap interval, and the acceptance criterion "cloned beats rule
baseline" is stated as a distribution (here: never on any draw) rather than
a one-row point. The trade is that it costs a per-seed evaluation harness —
the stage 04 and 05 runs recorded aggregate rates only, so this detour
re-simulates per seed — and per-seed records in `runs/`, and it can make a
verdict look worse before it looks better: a subset relation is a stronger
negative than a rate tie, which is exactly what an honest report owes.

## Who owns the loop

- **The report owner** owns the per-seed records and the interval: a
  verdict without a winner-set overlap and a bootstrap CI is a point
  estimate masquerading as a conclusion.
- **The stage owners** own storing per-seed outcomes, not just aggregate
  rates, in their `runs/` records; a report cannot resample what was never
  recorded.
- **The mission owner** owns the decision the verdict feeds: a NOT-MET that
  is subset containment says "discard or retrain", while a NOT-MET that is
  disjoint complementarity says "keep both" — different next actions, same
  rate cell.

## Evidence boundary

The bootstrap is measured on this simulator's generators and this clone;
2,000 draws make the interval tight but not exact, and the interval covers
scenario sampling only — not a different render, expert, or training seed.
The subset relation is a property of this clone on these 50 scenarios; a
clone trained differently (the [rebalance detour](../../03-behavior-cloning/when-the-rebalance-fixes-the-metric/)
shows oversampling lifts completion to 0.44) changes the set without
changing the method. External claims are dated and cited, never
re-measured here. Numbers trace to
[`runs/2026-08-08-verdict-bootstrap.json`](runs/2026-08-08-verdict-bootstrap.json).

## Check your mental model

Answer each before opening it.

**1. Why is a zero-width confidence interval not a broken measurement?**

<details>
<summary>Answer</summary>

Because the clone and the floor agree on every one of the 50 seeds — same
14 winners, same 36 failures. Any resample of seeds preserves that
within-seed agreement, so the paired difference is identically zero on all
2,000 draws. The zero-width CI is the signature of a deterministic
per-seed containment, not of luck or a bug.

</details>

**2. When would a near-tie rate table hide a complementarity that
resampling would reveal?**

<details>
<summary>Answer</summary>

If two policies completed the same number of scenarios on disjoint winner
sets — 14 and 14 with no shared winners — the rate cells would still read
0.28 vs 0.28, but a system that kept both policies would complete the
union, roughly 28 scenarios. The aggregate verdict "tie" would then be
misleading in the opposite direction from this run: it would hide that the
bar is clearable by blending. The winner-set IoU is the check that
distinguishes the two worlds.

</details>

**3. Which verdicts in the stage-06 table are most uncertain under
resampling?**

<details>
<summary>Answer</summary>

The MET rows, not the NOT-MET row. The clone-vs-floor comparison has
zero-width CI because the policies coincide per seed. The expert-vs-clone
gaps are reliably positive — P > 0 on every draw — but their size is
uncertain: 95% CI [0.50, 0.78] in-distribution and [0.60, 0.86] on hard.
The report's point estimates (0.64 and 0.74) are the least certain numbers
in the table, even though the conclusions they support are the ones that
pass.

</details>

## Next

Back to [stage 06](../). The subset relation this detour exposes is the
same no-dodge behavior the
[open-loop-lies detour](../../04-closed-loop-eval/when-the-open-loop-lies/)
measures on expert frames, and the hard side's 36 timeouts are profiled in
[when the policy stalls](../../05-harder-scenarios/when-the-policy-stalls/);
the [rebalance detour](../../03-behavior-cloning/when-the-rebalance-fixes-the-metric/)
shows what it takes to make the clone solve scenarios the floor fails.
