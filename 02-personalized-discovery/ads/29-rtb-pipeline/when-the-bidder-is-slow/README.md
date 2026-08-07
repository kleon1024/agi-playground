---
status: verified
level: applied
base: scratch
label: When the bidder is slow
verified: 2026-08-07
---

# Latency is a bidder's cost of entry

**Question:** [stage 29's RTB pipeline](../) runs the auction inside a
deadline. This chapter reads the executed deadline check and asks what
the timeout does to the bidder population.

**Before this:** [stage 29 — RTB pipeline](../) and its executed
latency-budget model.

## The deadline, executed

The run ([record](runs/2026-08-07-slow-bidder-read.md)) checks three
bidders against the 100ms deadline:

| bidder | response time | outcome |
|---|---:|---|
| a | 40 ms | bid in time |
| b | 95 ms | bid in time |
| c | 130 ms | TIMED OUT |

## The reading

bidder c loses the auction not on price but on speed. The timeout is a
selection mechanism: bids that arrive late cannot win, and a slow
bidder is invisible to the exchange no matter how good its price is.
Latency is a bidder's cost of entry — the exchange's deadline filters
the bidder population before the auction's value comparison ever runs.
That is why stage 29's pipeline engineering exists: the bid that never
arrives is a bid that cannot win.

## Evidence boundary

The executed deadline check over three declared response times
(illustrative, deterministic). It demonstrates the mechanism; real
bidder selection also includes the exchange's timeout policy and the
distribution of bidder latencies, which is measured per exchange.

## Check your mental model

Answer each before opening it.

**1. Why can the best-priced bidder still lose?**

<details>
<summary>Answer</summary>

Because price is only evaluated for bids that arrive. A 130ms bidder is
timed out before the auction runs, so its price never enters the
comparison. The deadline is a pre-filter: speed decides who competes,
price decides who wins among those who do.

</details>

**2. What does this mean for a bidder's engineering priorities?**

<details>
<summary>Answer</summary>

Latency comes before bid sophistication. A bidder whose pipeline
exceeds the deadline is invisible however good its model — the
slow-bidder case is eliminated at the boundary. RTB engineering is
first about fitting the pipeline inside the deadline (stage 29's
budget), then about improving the bid that fits.

</details>

## Next

Back to [stage 29](../), where the bid must arrive in 100ms. The
[exchange-timeout detour](../when-the-exchange-times-out/) prices the
other side: requests the exchange cannot fill.
