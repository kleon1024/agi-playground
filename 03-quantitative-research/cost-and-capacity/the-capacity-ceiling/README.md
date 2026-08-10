---
status: verified
level: applied
base: scratch
label: The capacity ceiling
verified: 2026-08-06
---

# Where the book stops: liquidity, then cost

**Question:** [stage 04's cost and capacity](../) prices a portfolio against
measured liquidity and assumed costs. This chapter reads the recorded run
and asks where the book stops growing.

**Before this:** [stage 04's cost and capacity](../) and its recorded run.

## The numbers, read

The run ([record](runs/2026-08-06-capacity-read.md)) reads the recorded
values:

| number | value |
|---|---|
| ADV | USD 12,578,055,538 |
| daily volatility | 1.7839% |
| 10m book | 0.0398% participation, 0.2780% annual cost |
| discrete-sweep peak book | USD 25,156,111,076 |
| total-return breakeven book | USD 125,780,555,379 |

## Two readings

**The book stops in two places, and they are different.** The
discrete-sweep peak (USD 25bn) is where participation in a single
rebalance becomes so large the sweep's capacity bound bites — the liquidity
ceiling. The total-return breakeven (USD 125bn) is where annual cost eats
the entire paper return — the cost ceiling. A strategy can be liquid
enough and still unprofitable; the two numbers are the two questions.

**Measured inputs, declared assumptions — the boundary is the point.** ADV
and volatility are measured; spread, commission, gross return, cadence,
and impact are declared assumptions, and the run says so. The capacity
numbers are therefore bounds on a model, not execution evidence — which is
exactly what a pre-trade capacity screen should be, and what the chapter's
evidence boundary insists on.

## The fix and its trade

The fix is the pre-trade capacity screen the run demonstrates: separate
the liquidity ceiling (the discrete-sweep peak, USD 25bn, where
participation in a single rebalance bites) from the cost ceiling (the
total-return breakeven, USD 125bn, where annual cost eats the declared 12%
paper return), and report both as bounds on a model, not execution
evidence. A strategy can be liquid enough and still unprofitable; the two
numbers are the two questions, and the screen exists so the sizing decision
asks both before committing capital.

The trade is that the screen is only as good as its declared assumptions.
ADV and volatility are measured; spread, commission, gross return, cadence,
and the impact model are declared — and the impact coefficient is the one
that most determines where the ceilings land. Square-root participation
impact is an empirical regularity, not a physical law: Almgren, Thum,
Hauptmann, and Li, "Direct Estimation of Equity Market Impact," 2005, fit
a different exponent on one desk dataset, and Tóth et al., "Anomalous
Price Impact," 2011, motivate approximate square-root behavior — so the
form is useful but its coefficient must be fitted from the firm's own
fills. A screen run on a borrowed coefficient is a model bound, not a
capacity answer, which is exactly why the chapter's evidence boundary
insists on the distinction.

## Who owns the loop

- **Capacity/risk** owns the screen and its assumptions: the declared
  spread, commission, gross, cadence, and impact model, versioned with the
  run so a reviewer can see what the ceilings were computed under.
- **Execution/trading** owns the fills data that re-fits the impact
  coefficient — the step that turns a model bound into an executable
  capacity number.
- **Research** owns the paper return input (the declared gross) and
  consumes the screen's answer to decide whether the strategy is sizeable
  at all.

When the screen is run on a borrowed impact coefficient, the USD 25bn and
USD 125bn ceilings read like measured facts and behave like assumptions —
and the sizing decision inherits a number the firm never fitted.

## Evidence boundary

The recorded cost-and-capacity run (AAPL, 2y window, 500 bars, one set of
declared assumptions). It reads that artifact; it does not re-fetch and the
USD figures are model outputs under the disclosed assumptions, not fitted
or observed execution.

## Check your mental model

Answer each before opening it.

**1. Why are there two capacity ceilings instead of one?**

<details>
<summary>Answer</summary>

Because capacity fails for two different reasons. The discrete-sweep peak
is the liquidity failure — beyond it, the book cannot be rebalanced without
moving the market. The breakeven is the cost failure — beyond it, annual
cost exceeds the paper return even though the book is still tradeable. A
book stops being viable at whichever ceiling comes first, and the two
numbers are what make that legible.

</details>

**2. What does 0.2780% annual cost on a 10m book tell you?**

<details>
<summary>Answer</summary>

That at the small size, cost is a rounding error relative to any real
return — the book's problem is not cost yet. The breakeven number is where
that stops being true: as the book grows, participation and cost scale, and
the breakeven (USD 125bn) is the size at which they consume the entire
declared 12% paper return. The 10m row is the "cost is fine" end of the
curve; the breakeven is the other end.

</details>

## Next

Back to [stage 04](../), or to
[where the book stops making money](../when-the-book-stops-making-money/)
which reads the same run's capacity curve.
