---
status: verified
level: applied
base: scratch
label: When the model outruns the budget
verified: 2026-08-08
---

# The 25ms inference slot has a tail of its own

**Question:** [stage 29's RTB pipeline](../) runs the auction inside a
100ms deadline. This chapter reads the executed model-fallback audit
and asks what happens when the inference model — the 25ms slot in the
stage's budget — is itself too slow for its share.

**Before this:** [stage 29 — RTB pipeline](../) and its executed
latency-budget model, and [shared stage 08](../../../shared/08-serving/)
for the tail discipline that pipeline ran.

## The fallback, executed

The run ([record](runs/2026-08-08-model-fallback.md)) serves 10,000
requests (fixed seed) with a heavy model (median 25ms, heavy tail) and
a cheap fallback (median 8ms), under two policies:

| policy | p50 | p95 | p99 | timeouts |
|---|---:|---:|---:|---:|
| heavy-only | 81.5ms | 118.7ms | 140.3ms | 1,800 (18.0%) |
| cascade | 75.5ms | 103.9ms | 125.3ms | 693 (6.9%) |

Fallback share: 33.1 percent of requests served by the cheap model.

## The failure mode, named

**The model stage is a tail inside the pipeline.** The stage's budget
gives inference a 25ms slot, but the slot is a median, not a
guarantee. A heavy model's lognormal tail runs long — p99 at 140.3ms
in the heavy-only run — and every one of those requests loses the
deadline before the bid is ever compared. The mean hides it: the
heavy-only mean is 84.3ms while 18 percent of requests time out. The
same tail arithmetic the stage's audit applied to the total pipeline
applies inside the model stage itself.

**The expensive requests are also the least certain.** The requests
that arrive late at the model stage are the ones whose context is
strained — slow profile lookup, cold features, a straggling queue. The
cascade serves those with the cheap model, which is exactly where a
less accurate bid matters least and a fast one matters most: a
timeout earns nothing, a cheap bid at least competes. The fallback
share (33.1 percent) is the quality bill, paid on the worst-tail
traffic (Yuan, Wang & Zhao, 2013, arXiv:1306.6542, measure a
production ad exchange and report the latency and timeout pressure
that real-time bidding faces; OpenRTB 2.5, `tmax`: "Maximum time in
milliseconds the exchange allows for bids to be received including
Internet latency to avoid timeout", so the deadline the model must fit
is the exchange's, not the platform's).

**The deadline is a tail constraint, and the margin is the budget.**
The stage's 20ms margin absorbs the p95 but not the p99; the shared
serving stage measured the same shape for the recommendation funnel —
parallel no-cache mean 31.22ms and p95 49.31ms, serial 52.73 and
72.71ms, cached 7.00 and 34.52ms — where the p95 is the operating
number and the cache is the tail's first line of defense
([shared/08-serving](../../../shared/08-serving/)). In RTB the exchange
enforces the tail: the request that does not fit the deadline is
gone, however good the model would have been.

## Who owns the loop

- **The model and serving team** owns the inference budget: model
  latency at p99, the fallback decision, and the cascade threshold. It
  owns the tail-inside-the-pipeline failure — the heavy-only run
  timed out 18 percent of requests with a p99 of 140.3ms.
- **The feature and data team** owns the pre-model latency: profile
  lookup and context features, and the cache that shortens them. It
  owns the straggler failure — the late-arriving requests that force
  the fallback are the ones with slow feature reads (shared/08-serving
  measured the cache's effect: p95 34.52ms cached against 49.31ms
  parallel).
- **The RTB engineering and exchange-facing team** owns the deadline
  contract: the exchange's `tmax`, the timeout policy, and the
  fill-rate consequence of every missed bid. It owns the lost-auction
  failure — 18 percent of requests in the heavy-only run are slots
  that sell nothing (Yuan, Wang & Zhao, 2013, measure the timeout
  pressure of a production exchange).

When the ownership is implicit, the model team ships the heavy model
on its median latency, the feature team ships no cache, and the
exchange times out the tail — 18 percent of the platform's demand
never competes, invisible in the mean.

## The fix and its trade

The measured fix is the cascade: when the request arrives at the model
stage late, serve the cheap model instead of the heavy one. The
executed table is the trade: timeouts fall from 18.0 to 6.9 percent
and the p95 from 118.7 to 103.9ms, at the price of cheap-model bids on
33.1 percent of requests — the late, tail requests whose context is
least certain. The alternatives are the same shape on the other
stages: cache the profile and features so the pre-model stages
shrink (shared/08-serving's cache read), or size the model slot by
p99 so the heavy model fits the deadline it is given (Yuan, Wang &
Zhao, 2013; OpenRTB 2.5's `tmax` is the contract the sizing has to
meet). The trade is universal in RTB: the deadline is fixed, so every
millisecond of quality costs either a timeout or a cheaper model —
the engineering question is where the fallback boundary sits.

## Evidence boundary

The executed audit uses declared lognormal latencies over 10,000
synthetic requests (fixed seed). It demonstrates the cascade
mechanism and its trade; real fallback thresholds are tuned on
measured per-stage latency distributions and the exchange's actual
timeout policy, and the quality cost of the cheap model is measured
on bid win rates, not assumed.

## Check your mental model

Answer each before opening it.

**1. Why does the heavy model's median latency not tell you whether it
fits the budget?**

<details>
<summary>Answer</summary>

Because the deadline is a tail constraint and the model has a tail.
The heavy model's median is 25ms — inside its slot — but its p99 runs
to 140ms end to end, and the heavy-only run timed out 18 percent of
requests. The mean (84.3ms) and the median (81.5ms) both look fine
while the tail loses the auction. Size the slot by p99, not by
median.

</details>

**2. What does the cascade trade for the recovered timeouts?**

<details>
<summary>Answer</summary>

Bid quality on the worst-tail requests. The cascade serves the cheap
model when the request arrives late at the model stage — 33.1 percent
of requests in the audit — cutting timeouts from 18.0 to 6.9 percent.
Those requests get a less accurate bid, but a late heavy bid would
have won nothing anyway; the cheap bid at least competes. The
fallback boundary is where the platform trades a guaranteed timeout
for a cheaper, noisier bid.

</details>

## Next

Back to [stage 29](../), where the bid must arrive in 100ms. The
[slow-bidder detour](../when-the-bidder-is-slow/) shows the bidder-side
deadline, and the [exchange-timeout detour](../when-the-exchange-times-out/)
prices the slots the deadline costs.
