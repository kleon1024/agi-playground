---
status: verified
level: applied
base: scratch
label: When the refusal names everything
verified: 2026-08-06
---

# The refusal that names everything

**Question:** [mission 03's report](../) returns `CANNOT DETERMINE` — it
refuses to render a verdict. A refusal is only useful if it says what is
missing; this chapter reads the refusal and groups the 18 named inputs by
what each would establish.

**Before this:** [mission 03's report](../) and its recorded refusal
(2026-07-27).

## The refusal, re-run and grouped

The run ([record](runs/2026-08-06-refusal-read.md)) re-runs the stage's own
report against the real current state — the same `CANNOT DETERMINE` — and
groups the named inputs:

| group | what it would establish |
|---|---|
| baselines | buy-and-hold (passive floor) and momentum (the bar that actually has to be beaten), per fold |
| candidate | net/gross Sharpe per fold, deflated Sharpe + trial count, drawdown, capacity, point-in-time and survivorship integrity |
| cost | real dollars per fold, modeled transaction cost, modeled market impact |
| latency | p50, p95 |
| regimes | the mandatory failure-case breakdown |

## Two readings

**A refusal is a checklist, not a wall.** The 18 missing inputs are not 18
random fields; they are the contract's acceptance conditions named one by
one. A report that cannot say which inputs are missing has not refused, it
has hidden. The distinction is the whole lesson of the stage's three-way
verdict: `CANNOT DETERMINE` is a first-class result that names exactly what
would turn it into MET or NOT MET.

**The refusal is the correct output for this mission's current state.** No
stage has produced the integrated outcome artifact yet — the signal,
ranking, validation, and cost stages exist as implementations and runs, but
their outputs were never combined into the artifact `mission.yaml`
requires. Manufacturing a conclusion from partial artifacts would be worse
than saying nothing, and the stage says so in its own refusal text.

## Evidence boundary

The stage's own report re-run against the real current state; the refusal
and its 18 named inputs match the recorded 2026-07-27 run. It does not
change the mission's status and does not claim any of the missing inputs
exist.

## Check your mental model

Answer each before opening it.

**1. Stages 01-04 have real runs. Why is the report still CANNOT
DETERMINE?**

<details>
<summary>Answer</summary>

Because a mission verdict needs an integrated outcome artifact — per-fold
candidate and baseline Sharpes, deflated Sharpe with trial count, guardrail
inputs, cost, latency, regimes — all in one place, produced by one contract.
Stage-level mechanism runs are deliberate insufficient evidence for a
mission claim; combining them by hand after the fact is how a verdict gets
softened without anyone noticing.

</details>

**2. Why does the refusal name 18 inputs instead of one summary line?**

<details>
<summary>Answer</summary>

Because each missing input is a different way the mission could fail. A
deflated-Sharpe input missing is a multiple-testing failure waiting to
happen; a missing point-in-time input is survivorship bias; a missing cost
input is a strategy that only works on paper. Naming each one tells the
next system exactly which baseline, guardrail, or budget stopped complexity
from becoming value.

</details>

## Next

Back to [mission 03's report](../), or to
[when breadth inflates the winner](../../01-signal-research/when-breadth-inflates-the-winner/),
which is the mechanism behind the deflated-Sharpe input the refusal names.
