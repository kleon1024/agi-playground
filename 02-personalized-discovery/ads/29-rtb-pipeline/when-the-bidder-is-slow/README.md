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

## The fix and its trade

The bidder's fix is to fit the whole pipeline inside the exchange's
`tmax`: the deadline is the contract, so each stage gets a p99 budget
whose sum fits the bid before the deadline, not a median budget whose
tail crosses it. Stage 29's executed budget does exactly this — the
per-stage table allocates the 100ms deadline so that the p99 of every
stage lands inside its slot — and shared/08-serving's cache read is the
first lever: a profile or feature served from cache turns a 30ms stage
into a 1ms stage and buys margin for the stages that cannot cache
(OpenRTB 2.5 defines `tmax` as "Maximum time in milliseconds the
exchange allows for bids to be received including Internet latency to
avoid timeout"; Yuan, Wang & Zhao, 2013, arXiv:1306.6542, measure a
production ad exchange and report the latency pressure that RTB
pipelines face). The trade is that p99 budgeting is strictness paid
everywhere for a failure that happens rarely: stages that are usually
fast are forced into their p99 slot, and the margin you reserve is
latency you are not spending on a better bid. The alternative — fit
the median and hope the tail — is the exact failure the audit measures:
the bidder that is late loses regardless of price.

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
