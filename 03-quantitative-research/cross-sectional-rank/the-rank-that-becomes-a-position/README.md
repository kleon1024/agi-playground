---
status: verified
level: applied
base: scratch
label: The rank that becomes a position
verified: 2026-08-06
---

# The sizing rule IS the strategy

**Question:** [stage 02's cross-sectional rank](../) turns a signal into a
portfolio. The model is not one formula — it is a pipeline (signal, rank,
weight, position) — and this chapter dissects the stage where the strategy
actually lives: the sizing rule.

**Before this:** [stage 02's cross-sectional rank](../) and its recorded
run.

## The pipeline, read

The run ([record](runs/2026-08-06-rank-anatomy.md)) reads the recorded
stage-02 run, which held one momentum signal family fixed and measured four
sizing rules:

| rule | HHI | turnover | paper Sharpe | cap violations |
|---|---:|---:|---:|---:|
| Equal-weight decile | 0.6667 | 0.638 | -0.68 | 7 |
| Rank-proportional | 0.1776 | 0.348 | -1.05 | 47 |
| Signal-proportional | 0.2243 | 0.369 | -1.20 | 35 |
| Volatility-scaled | 0.1952 | 0.404 | -0.83 | 43 |

<!-- interactive: RankToPositionAnatomy -->

## The structure, named

The pipeline has four stages and one decision point:

1. **Signal** — one score per name (here, a momentum family held fixed).
2. **Cross-sectional rank** — order the scores, drop the absolute values.
3. **Weight** — the sizing rule maps rank/score to a portfolio weight.
4. **Position** — the constraint stage: cap, sector de-mean, rebalance.

The rule at stage 3 is the strategy. Equal-weight says only the tails carry
useful order — it concentrates (HHI 0.6667) but holds few names.
Rank-proportional says order matters across the full universe — it spreads
(HHI 0.1776) but churns 0.348 of the book monthly. The same signal, four
different portfolios, four different Sharpe numbers: the anatomy is that
the strategy is chosen at stage 3, not invented at stage 1.

## The constraint stage is why the anatomy matters

Every rule breaks the 10% cap after naive cap-then-sector-de-mean (7 to 47
violations): applying the cap and the sector constraint *sequentially*
re-breaks the cap, because de-meaning moves weights back above it. That is
the recorded reason a joint constrained optimizer is necessary — the
pipeline's last stage is not a clean-up step, it is part of the strategy,
and doing it wrong undoes the sizing rule the anatomy was built around.

## The fix and its trade

The fix is a joint constrained optimizer: cap and sector de-mean enforced
in one pass, instead of cap-then-de-mean applied sequentially. The recorded
violations are the measured cost of the sequential order — 7 to 47
re-breaches, because de-meaning pushes names back above the cap the first
step already applied.

The trade is transparency and speed for correctness. A joint optimizer
hides constraint interaction inside a solver: the pipeline is harder to
audit by hand, and it can return feasible weights that surprise the
researcher who built the two-step version (a cap that never binds, a
sector mean that overrides a deliberate tilt). It also costs a solver
dependency and a slower pipeline than two sequential vector operations.
But the alternative is a strategy whose realized positions do not match its
declared constraints — every rule here measured 7 to 47 violations, which
means the paper Sharpe was computed on a book the policy did not actually
allow. A real portfolio-construction team makes the same trade: constraints
are part of the strategy, and they are enforced jointly or not at all.

## Who owns the loop

- **Research** owns the sizing rule at stage 3 — the anatomy's decision
  point where the strategy is actually chosen.
- **Portfolio construction** owns the constraint pipeline: the cap policy,
  the sector de-mean, and the joint optimizer that enforces both. Its
  contract is that realized positions match declared constraints.
- **Risk** owns the cap values and the violation check that audits the
  optimizer's output — the same count the recorded run reports (7 to 47),
  run as a standing check rather than a one-off.

When the pipeline is sequential, the cap is a policy that its own next step
silently undoes, and the backtest is measured on positions the strategy was
never allowed to hold.

## Evidence boundary

The recorded stage-02 run (30 names, 24 monthly rebalances, cost-free
paper diagnostics, one signal family). It reads that artifact; it does not
re-run the fetch (live data would move the window) and the Sharpe values
are upper-bound mechanics, not live-performance evidence.

## Check your mental model

Answer each before opening it.

**1. Why is rank-proportional's Sharpe worse than equal-weight's despite
lower concentration?**

<details>
<summary>Answer</summary>

Because concentration and return are different axes. Equal-weight's high
concentration (0.6667) means it bets on the tails, which happened to carry
this panel's signal; rank-proportional spreads across every name, which
dilutes the tail signal and pays more turnover (0.348) to do it. The
anatomy's point is that the rule determines the risk/return profile before
any return is realized — lower HHI is not automatically better, it is
*different*.

</details>

**2. Why does the cap break even though it was applied?**

<details>
<summary>Answer</summary>

Because cap-then-de-mean is sequential, not joint. Capping pulls the
over-weight names down to 10%; sector de-meaning then shifts every weight
in a sector by that sector's mean, which pushes some names back above the
cap. The fix is a single optimizer that enforces both constraints at once —
the recorded violations (7 to 47) are the measured cost of doing them in
the wrong order.

</details>

## Next

Back to [stage 02's cross-sectional rank](../), or forward to
[stage 04 — cost and capacity](../../04-cost-and-capacity/) where the
paper portfolio meets trading costs.
