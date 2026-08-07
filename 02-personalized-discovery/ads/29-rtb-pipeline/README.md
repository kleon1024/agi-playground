---
status: verified
level: applied
base: scratch
label: RTB pipeline
verified: 2026-08-07
---

# The p95 fits the deadline; the p99 loses the auction

**Question:** [stage 28's auction](../28-auction-revenue/) assumed bids
arrive. This stage asks what it takes to get a bid out in time, and
answers: real-time bidding is a latency pipeline with a hard deadline,
and the audit shows the mean and even the p95 fit while the p99 blows
the deadline — every one of those requests is a slot with no bid.

**Before this:** [stage 28 — auction revenue](../28-auction-revenue/)
for the auction, and [stage 08 — serving](../../shared/08-serving/) for the
latency discipline this mission established.

## The mechanism, executed

The run ([record](runs/2026-08-07-rtb-pipeline.md)) splits the 100ms
deadline across the pipeline:

| stage | ms |
|---|---:|
| request parse | 5 |
| user profile lookup | 20 |
| context features | 10 |
| model inference | 25 |
| bid decision | 15 |
| response send | 5 |
| total | 80 |
| margin | 20 |

Five stages consume 80ms, leaving 20ms of margin. Every stage is a
latency source and a potential timeout — the pipeline's p95 is the sum
of its worst stages, which is why RTB engineering is mostly about
keeping the tail inside the budget. The margin is what absorbs jitter,
and when a stage blows it, the [slow-bidder detour](when-the-bidder-is-slow/)
shows what happens: the bid arrives late and is invisible, however good
its price.

## The failure mode, named and audited

**The p99 loses the auction.** The audit
([record](runs/2026-08-08-tail-latency.md)) draws 20,000 requests
(fixed seed) where each stage's latency is lognormal with its nominal
time as the median and a declared spread:

| total vs 100ms | value |
|---|---:|
| p50 | 81.7ms |
| p90 | 95.3ms |
| p95 | 99.5ms |
| p99 | 108.2ms |
| mean | 82.4ms |
| timed out | 933 (4.7%) |

The verdict is measured: the p50 sits near the nominal 80ms and the
p95 fits inside the margin — but the p99 blows the deadline at 108.2ms,
and 933 of 20,000 requests time out. The mean hides it: 82.4ms looks
healthy while 4.7 percent of requests lose the auction before the bid
is compared. The deadline is a tail constraint, and the margin has to
be sized for the p99, not the p95 (Yuan, Wang & Zhao, 2013,
arXiv:1306.6542, measure a production ad exchange under real-time
latency and timeout pressure; OpenRTB 2.5's `tmax` is the contract: the
exchange sets the maximum time for bids "including Internet latency to
avoid timeout").

**The model stage has a tail of its own.** The
[model-outruns-the-budget detour](when-the-model-outruns-the-budget/)
isolates the 25ms inference slot: a heavy model's p99 runs to 140ms
end to end, timing out 18.0 percent of requests; the cascade — a cheap
fallback model for late-arriving requests — cuts timeouts to 6.9
percent at the price of cheap bids on 33.1 percent of requests, the
worst-tail traffic whose context is least certain.

**Every timeout is a slot that sells nothing.** The
[exchange-timeout detour](when-the-exchange-times-out/) prices the
exchange side: a 5 percent timeout rate leaves 50,000 of a million
requests unfilled, so timeout rate is a revenue metric, not an
availability footnote. The [slow-bidder detour](when-the-bidder-is-slow/)
shows the bidder side: a 130ms bidder is timed out whatever its price,
so latency is a bidder's cost of entry.

## Who owns the loop

The deadline only holds if someone is accountable at each side of the
latency loop, and each owner is tied to one of the failure modes above:

- **The RTB engineering and exchange-facing team** owns the deadline
  contract: the exchange's `tmax`, the timeout policy, and the
  fill-rate consequence of every missed bid. It owns the lost-auction
  failure — the audit measured 933 timed-out requests in 20,000, and
  the exchange detour prices 50,000 unfilled slots at a 5 percent rate
  (Yuan, Wang & Zhao, 2013; OpenRTB 2.5).
- **The model and serving team** owns the inference budget: model
  latency at p99, the fallback decision, and the cascade threshold. It
  owns the tail-inside-the-pipeline failure — the detour measured
  heavy-only timeouts at 18.0 percent against the cascade's 6.9.
- **The feature and data team** owns the pre-model stages: profile
  lookup, context features, and the cache that shortens them. It owns
  the straggler failure — late-arriving requests are the ones with slow
  feature reads, and shared/08-serving measured the cache's effect
  (p95 34.52ms cached against 49.31ms parallel).

When the ownership is implicit, the engineering team sizes the budget
on nominal times, the model team ships on median latency, and the tail
times out quietly — 4.7 percent of demand never competes in the audit,
invisible in the mean.

## Why this belongs in the mission

This is the ads track's serving stage — the direct analogue of [stage
08](../../shared/08-serving/) for recommendation. Both are the mission's latency
guardrail made concrete: the p95 budget is a constraint, not
decoration, and in RTB it is the exchange's deadline, not the
platform's own target, that decides whether the bid exists at all.
The audit adds the industrial detail: the deadline is a tail
constraint, the margin is a tail budget, and the fallback is where
quality trades against survival.

## Evidence boundary

The executed budget split and the audit's 20,000 synthetic requests
(fixed seed, declared lognormal spreads) are illustrative and
deterministic. They demonstrate the allocation and the tail
arithmetic; real RTB budgets are measured per stage at p99, timeout
policy is per exchange, and the fallback threshold is tuned on
measured distributions rather than declared.

## Check your mental model

Answer each before opening it.

**1. Why is the margin the point of the exercise?**

<details>
<summary>Answer</summary>

Because the deadline is fixed and the stages jitter. The 20ms margin is
what absorbs the tail — if the stages always ran at their nominal
times, the budget would be trivial. RTB engineering is keeping the sum
of the worst stages inside the deadline, which is a tail problem, not an
average one.

</details>

**2. Your latency dashboard shows a healthy 82ms mean, but fill is
down. Where do you look?**

<details>
<summary>Answer</summary>

At the p99 before the mean. The audit's mean is 82.4ms while the p99 is
108.2ms and 933 of 20,000 requests exceed the deadline. The mean hides
the tail: every timed-out request is a slot with no bid, and the
deadline is a tail constraint. Read the p99 against the exchange's
`tmax` — that is the contract the pipeline has to fit.

</details>

**3. What does a timeout do to the auction?**

<details>
<summary>Answer</summary>

It removes the bid. A bid that arrives after the deadline cannot win,
whatever its price — the slow-bidder detour shows a 130ms bidder timed
out. And every timed-out request is a slot that runs without a bid: the
exchange-timeout detour prices 50,000 unfilled requests at a 5%
timeout rate on a million-request day.

</details>

## Next

Forward to [stage 30 — ads measurement](../30-ads-measurement/) where
the ads track's outcome is measured.

A detour from here: [latency is a bidder's cost of
entry](when-the-bidder-is-slow/) — the executed deadline read: a 40ms
and a 95ms bidder make the 100ms cutoff while a 130ms bidder is timed
out, so a slow bidder is invisible however good its price.

Another detour: [every timeout is a slot that sells
nothing](when-the-exchange-times-out/) — the executed pricing read: a
5% timeout rate leaves 50,000 of a million requests unfilled, so
timeout rate is a revenue metric, not an availability footnote.

A third detour: [the 25ms inference slot has a tail of its
own](when-the-model-outruns-the-budget/) — the executed cascade read:
heavy-model-only times out 18.0 percent of requests at a p99 of
140ms, while a cheap fallback cuts timeouts to 6.9 percent at the
price of cheaper bids on 33.1 percent of the worst-tail traffic.
