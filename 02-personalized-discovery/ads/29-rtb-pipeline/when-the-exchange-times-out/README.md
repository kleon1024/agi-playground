---
status: verified
level: applied
base: scratch
label: When the exchange times out
verified: 2026-08-07
---

# Every timeout is a slot that sells nothing

**Question:** [stage 29's RTB pipeline](../) runs bids inside a
deadline. This chapter reads the executed timeout pricing and asks what
the exchange's timeout rate costs.

**Before this:** [stage 29 — RTB pipeline](../) and its executed
latency-budget model.

## The cost, executed

The run ([record](runs/2026-08-07-exchange-timeout-read.md)) prices the
timeout rate on a million-request day:

| timeout rate | requests unfilled |
|---|---:|
| 1% | 10,000 |
| 5% | 50,000 |
| 10% | 100,000 |

## The reading

Every timed-out request is a slot that runs without a bid — the
publisher's inventory, the exchange's revenue, and the advertiser's
reach all miss together. A 5% timeout rate leaves 50,000 of a million
requests unfilled. Timeout rate is a revenue metric, not an
availability footnote: it is the exchange-side version of the
[slow-bidder detour](../when-the-bidder-is-slow/) — one bidder's
latency is that bidder's loss, but the exchange's timeout rate is
everyone's loss.

## The fix and its trade

The exchange's lever is the timeout policy itself: how long `tmax`
gives bidders before the slot is closed. A longer `tmax` raises fill —
more bidders arrive, more auctions have a winner — but it is paid in
latency for the user who is waiting on the ad decision, and the winning
bids arrive late in the window, so the page request gets the slowest
possible bidder. A shorter `tmax` protects the user's wait but
filters out the slower bidder population, cutting competition and
fill (OpenRTB 2.5's `tmax`: "Maximum time in milliseconds the exchange
allows for bids to be received including Internet latency to avoid
timeout"; Yuan, Wang & Zhao, 2013, arXiv:1306.6542, measure the
timeout pressure real exchanges run under). The trade is a margin
sizing decision, not a reliability checkbox: the exchange sets `tmax`
from its own p99 on the bidder-latency distribution, and the stages
that pay it are the bidders whose pipelines are sized against a
stricter contract than the exchange's. The stage's own audit is the
bidder-side half of the same decision — the exchange that times out
at 5 percent is the exchange whose bidders sized their pipelines to
the old `tmax`.

## Evidence boundary

The executed pricing over a declared request volume (illustrative,
deterministic). It demonstrates the arithmetic; real timeout costs
include the publisher's fill-rate loss and the advertiser's missed
reach, which the exchange reports per slot type.

## Check your mental model

Answer each before opening it.

**1. Why is a timeout a revenue event rather than an operations
footnote?**

<details>
<summary>Answer</summary>

Because an unfilled slot earns nothing and serves no one. At a 5%
timeout rate that is 50,000 slots a day running without a bid — the
exchange forgoes its cut, the publisher's inventory is wasted, and the
advertiser misses reach. The rate is the top of a revenue funnel, not
an availability detail.

</details>

**2. How is the exchange's problem different from the bidder's?**

<details>
<summary>Answer</summary>

The bidder's timeout is individual — one bidder loses one auction. The
exchange's timeout is systemic: every request it fails to fill is a
slot nobody gets, which affects all three parties at once. The exchange
owns the deadline and the timeout policy, so its engineering problem is
keeping the whole pipeline's tail inside the budget, not any single
bidder's.

</details>

## Next

Back to [stage 29](../), where the bid must arrive in 100ms. The
[slow-bidder detour](../when-the-bidder-is-slow/) shows the bidder-side
cause of the same metric.
