---
status: verified
level: applied
base: none
label: When the book stops making money
verified: 2026-08-06
---

# Where does the book stop making money?

**Question:** [stage 04](../) prices the book's trading bill with an impact
model, and its recorded run reports one point plus a peak and a breakeven.
The full shape is a curve: net dollar return rises while costs are
negligible, peaks, and falls to negative. This chapter sweeps the whole
range so the cliff is visible, not summarized.

**Before this:** [stage 04's cost and capacity run](../) and its declared
assumptions.

## The curve, measured

The sweep ([record](runs/2026-08-06-capacity-cliff.md)) runs the stage's
model on the measured AAPL inputs (ADV, volatility) across book sizes:

| book | participation | annual cost | net pct | net dollar/year |
|---:|---:|---:|---:|---:|
| \$1B | 3.9% | 1.44% | 10.56% | \$106M |
| \$10B | 39.3% | 4.22% | 7.78% | \$778M |
| **\$31.6B** | 124% | 7.39% | 4.61% | **\$1,458M** |
| \$56B | 221% | 9.80% | 2.20% | \$1,235M |
| \$100B | 393% | 13.02% | -1.02% | -\$1,022M |

## Two readings

**Net dollar return peaks, then falls.** The book makes the most money at
around \$31.6B (about \$1.46B/year net), and every additional dollar beyond
that adds zero or negative profit. At \$100B the strategy loses money
despite a 12% gross — the cost curve ate the whole edge. The recorded run's
discrete-sweep peak (\$25.2B) lands near this log-grid one on the same
scenario; the grid differs, the cliff does not.

**The cliff is where participation crosses 100%.** Just past the peak, the
book's average participation reaches 124% of AAPL's daily dollar volume —
the strategy is asking the market to trade more than its daily volume.
That is the capacity limit made physical: beyond it, the impact model says
the strategy cannot be sized at all, which is why net return turns negative
shortly after.

The lesson: a strategy's capacity is a curve, not a number, and the 
research-scale signal ("works at \$10m") and the fund-scale question ("how
big can this get") are answered by different points on it.

## Evidence boundary

ADV and volatility are measured; spread, commission, impact exponent, gross,
and turnover are the stage's declared assumptions. One ticker, one scenario.
It shows the curve's shape and its peak on this setup; it does not claim
the peak transfers across markets or scenarios.

## Check your mental model

Answer each before opening it.

**1. Why does net dollar return fall while net percentage return also falls
monotonically?**

<details>
<summary>Answer</summary>

Net percentage return falls monotonically because cost only grows with book
size. Net dollar return is book size times net percentage: it rises while
the percentage fall is negligible, peaks where the marginal cost of another
dollar deployed equals its marginal gross, then falls — and turns negative
when cost exceeds gross. The peak is the point where the strategy's
cost curve crosses its return curve.

</details>

**2. What does participation above 100% mean, and why does it mark the
cliff?**

<details>
<summary>Answer</summary>

It means the book is asking to trade more than the market's entire daily
dollar volume — 124% at the peak row. The impact model treats this as
unimplementable: there is not enough liquidity to fill the orders at the
assumed participation rate, so the strategy cannot be sized past that
point. The percentage crossing 100% is the physical limit the cost curve
approaches asymptotically.

</details>

## Next

[Stage 05's report](../../05-report/): the cost-and-capacity guardrail held
against the mission's baselines and acceptance list.
