---
status: verified
level: applied
base: scratch
label: When the budget is tiny
verified: 2026-08-06
---

# Pacing cannot create a budget

**Question:** [stage 17's budget pacing](../) showed a 100-unit budget
surviving the day under a cap. This chapter runs the same controller on
tiny budgets and asks where pacing stops being able to help.

**Before this:** [stage 17 — budget pacing](../) and its executed
simulation.

## The boundary, executed

The run ([record](runs/2026-08-06-tiny-budget.md)) runs the pacing
controller (cap = budget / 8 hours) against one demand curve:

| budget | naive dark at | paced dark at |
|---:|---:|---:|
| 100 | hour 3 | hour 5 |
| 20 | hour 0 | hour 7 |
| 8 | hour 0 | hour 8 |

## Two readings

**Pacing stretches every budget but cannot create one.** At 20, the naive
spend is gone in the first hour while pacing survives the whole day on a
2.5/hour cap; at 8 the cap is 1/hour and the campaign barely delivers. The
same controller, the same demand — the difference is the budget itself.

**The floor is a sizing decision, not a pacing one.** The cap is
budget/hours, so when that quotient falls below the minimum viable spend,
the campaign cannot earn anything no matter how carefully it paces.
Pacing controls the distribution of a budget over time; sizing decides
whether the budget can buy delivery at all. The two questions are
different, and the tiny-budget case is where the confusion between them
becomes visible.

## Evidence boundary

The executed controller over three budgets and one hand-built demand curve
(illustrative, deterministic, fixed cap). It demonstrates the boundary;
real campaigns also face bid floors and auction competition, which change
the minimum viable budget.

## The fix and its trade

The measured fix is a sizing decision, not a pacing change: raise the
budget until the per-hour cap clears the minimum viable spend, or shrink
the targeting so the budget buys meaningful delivery (the stage audit's
cap sweep shows the same boundary from the other side — at multiplier
0.50 the cap under-delivers even a 100-unit budget). The trade is
reach versus relevance: a bigger budget buys more auctions but dilutes
per-auction efficiency, and narrower targeting keeps the budget viable
but caps the campaign's reach. Production bids with a win-rate model so
the minimum viable budget is derived from the auction, not guessed
(Zhang, Yuan & Wang, 2014, KDD, formulate optimal real-time bidding
for display advertising; Wang, Zhang & Yuan, 2017, *Foundations and
Trends in Information Retrieval* 11(4-5), survey bidding and pacing
together).

## Check your mental model

Answer each before opening it.

**1. Why does pacing fail at budget 8 when it works at 20?**

<details>
<summary>Answer</summary>

Because the cap is the budget divided by the day. At 20 the cap is 2.5 an
hour, enough to stay visible; at 8 it is 1 an hour, below the minimum the
auction can actually buy. The controller spreads exactly the same way in
both cases — what changes is that the spread amount falls under the
viability threshold. Pacing distributes; it does not raise the total.

</details>

**2. What would a production team change first at budget 8?**

<details>
<summary>Answer</summary>

Not the pacing algorithm — the budget or the campaign's reach. Either
raise the budget until the per-hour cap clears the minimum viable spend,
or shrink the targeting so the budget buys meaningful delivery. The
pacing controller's cap formula is unchanged; the sizing decision above
it is what moves the outcome. That is why the floor belongs to planning,
not to the delivery controller.

</details>

## Next

Back to [stage 17](../), or to
[the cap that binds when demand spikes](../when-delivery-varies/) for the
controller's behavior under unexpected demand.
