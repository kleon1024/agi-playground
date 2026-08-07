---
status: verified
level: applied
base: scratch
label: When the creative has no history
verified: 2026-08-08
---

# A creative with no history cannot be priced, and exploration alone does not fix that

**Question:** [stage 26's creative selection](../) scores creatives per
context. This chapter reads the executed cold-start sweep and asks how
a new creative — with no history — gets priced, and whether adding
exploration is enough.

**Before this:** [stage 26 — creative selection](../), the
[stale-creative detour](../when-the-creative-is-stale/) for the logged
CTR that hides wear, and the stage's
[wear-exploration audit](../) for the estimator's role.

## The sweep, executed

The run ([record](runs/2026-08-08-cold-start.md)) serves 20,000
placements (fixed seed) between a mature creative (lifetime CTR 0.06,
true rate decaying toward 0.025) and a new creative (true rate 0.04,
pessimistic cold-start prior 0.02), sweeping the exploration rate of
an epsilon-greedy policy whose estimator is the lifetime average:

| epsilon | served B | B estimate | clicks | clicks/imp |
|---:|---:|---:|---:|---:|
| 0.00 | 0 | 0.0200 | 625 | 0.0312 |
| 0.05 | 475 | 0.0435 | 667 | 0.0333 |
| 0.10 | 1,019 | 0.0357 | 645 | 0.0323 |
| 0.20 | 1,994 | 0.0358 | 653 | 0.0326 |

## The failure mode, named

**A new creative's price is a prior, and the prior is a guess.** The
new creative enters with no click history, so its estimate is whatever
the platform chooses — a pessimistic 0.02 here. With no exploration
(epsilon 0.00) the creative is never served, its estimate never
corrects, and the campaign earns 625 clicks all from the worn
incumbent. The cold-start failure is not the missing clicks; it is
that the estimate cannot move without traffic the policy never gives
it (Moriwaki, Nakagawa, Hisano & Ariu, 2019, arXiv:1908.08936,
measure wear-in and wear-out in ad creative selection and model the
creative's value as a function of served impressions, which is
exactly the signal a no-history estimate lacks).

**Exploration corrects the estimate but cannot switch the arm.** Raising
epsilon serves the new creative 475 to 1,994 placements and corrects
its estimate from 0.02 toward 0.04 — but clicks move only from 625 to
653 to 667. The corrected estimate still loses to the incumbent's
sticky 0.06 lifetime average, so the greedy arm keeps serving the
stale winner. Exploration learns the truth; the estimator decides
whether selection can use it. This is why the stage's audit found the
same wall: epsilon-greedy earned 645 clicks against the
recency-weighted estimator's 828.

**The exploration budget itself has a price.** Every placement served
to a cold creative is a placement not served to the incumbent, and if
the cold creative is actually worse, the budget is pure loss. The
sweep's flat click column is the optimistic version — here B is
genuinely better and exploration still cannot cash it in; a
pessimistic version would lose clicks to a bad creative during its
learning window (Agrawal & Goyal, 2012, arXiv:1203.4217, prove
Thompson sampling's regret bound, which is the formal statement of
how much exploration costs; He et al., 2014, ADKDD, describe the
online learning and feature pipeline Facebook runs for click
prediction, where cold creatives get controlled exploration traffic).

## Who owns the loop

- **The creative-ranking team** owns the estimate: the cold-start
  prior, the online learning rule, and the recency-aware update that
  lets the estimate move. It owns the sticky-estimator failure — the
  sweep measured a corrected 0.04 estimate that still lost to a
  lifetime 0.06 average, and the audit measured the fix recovering
  828 versus 635 clicks.
- **The delivery and exploration team** owns the traffic allocation:
  how much of the serving stream goes to cold creatives, and how it is
  targeted so the correction arrives before the creative's novelty
  wears off. It owns the learning cost — the sweep's epsilon dial is
  its control, and a wrong prior makes every explored placement
  expensive (Agrawal & Goyal, 2012).
- **The ads-measurement team** owns the verdict: per-creative CTR by
  age, the time-to-correct metric (how many placements a cold
  creative needs before its estimate stabilizes), and whether the
  corrected estimate ever changes what gets served. It owns the
  no-cash-in failure — exploration that learns but never switches is
  a budget spent with no selection change, which the flat click
  column measures.

When the ownership is implicit, the ranking team ships a pessimistic
prior, the delivery team never allocates cold-start traffic, and the
new creative waits forever while the campaign serves the worn
incumbent at 0.0312 clicks per impression — every measurement column
above is the cost.

## The fix and its trade

The measured fix pairs cold-start traffic with a recency-aware
estimate. The stage's audit shows the estimator side: a
recency-weighted EWMA or a Thompson posterior with decaying counts
lets selection see the wear and switch, earning 828 and 807 clicks
against greedy's 635. The exploration side is the sweep's epsilon
dial: enough traffic to correct the prior before novelty decays
(Moriwaki et al., 2019, model the creative's value as a function of
served impressions, which is the shape the correction must track). The
trade is the exploration bill itself: too little traffic and the
estimate never corrects (epsilon 0.00: B never served), too much and
a bad creative is served during its learning window at a loss
(Agrawal & Goyal, 2012, bound what that loss costs). The execution
answer in practice is a small targeted exploration budget — a few
percent of cold-creative traffic — with a recency-aware estimator, so
the corrected estimate can actually change the arm.

## Evidence boundary

The executed sweep uses two declared creatives, a declared wear
function, and Bernoulli clicks (fixed seed). It demonstrates the
correction-versus-switch gap; real cold-start design measures the
prior's calibration per creative family, the exploration budget per
market, and the time-to-correct on logged traffic.

## Check your mental model

Answer each before opening it.

**1. Why does exploration alone not fix creative selection here?**

<details>
<summary>Answer</summary>

Because exploration only feeds the estimator; it does not change what
the greedy arm reads. The sweep served the new creative 1,994
placements and corrected its estimate from 0.02 to 0.036, but that
still loses to the incumbent's sticky 0.06 lifetime average — so the
arm keeps serving the stale winner and clicks barely move (625 to
653). The estimator decides whether the corrected estimate can switch
selection, which is why the fix is recency-aware estimation, not
exploration alone.

</details>

**2. What does the flat click column tell you about the exploration
budget?**

<details>
<summary>Answer</summary>

That the budget is correcting an estimate nobody can use yet. The new
creative is genuinely better (true rate 0.04 versus the worn 0.025),
so the explored placements are not wasted clicks — but they change
nothing in what gets served until the estimator moves. Ship the
recency-aware estimator first; the exploration budget only pays off
once the corrected estimate can actually win the arm.

</details>

## Next

Back to [stage 26](../), where the creative is part of the ad's value.
The [stale-creative detour](../when-the-creative-is-stale/) shows the
logged-CTR confound the estimator must resist, and the
[context-changes detour](../when-the-creative-context-changes/) shows
the second feature the estimate needs.
