---
status: verified
level: applied
base: scratch
label: RTB pipeline
verified: 2026-08-07
---

# The bid that arrives too late never wins

**Question:** [stage 28's auction](../28-auction-revenue/) assumed bids
arrive. This stage asks what it takes to get a bid out in time, and
answers: real-time bidding is a latency pipeline with a hard deadline,
and the timeout is a selection mechanism.

**Before this:** [stage 28 — auction revenue](../28-auction-revenue/)
for the auction, and [stage 08 — serving](../08-serving/) for the
latency discipline this mission established.

## The budget, executed

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

## The mechanism, named

Five stages consume 80ms, leaving 20ms of margin. Every stage is a
latency source and a potential timeout — the pipeline's p95 is the sum
of its worst stages, which is why RTB engineering is mostly about
keeping the tail inside the budget. The margin is what absorbs jitter,
and when a stage blows it, the [slow-bidder detour](when-the-bidder-is-slow/)
shows what happens: the bid arrives late and is invisible, however good
its price.

## Why this belongs in the mission

This is the ads track's serving stage — the direct analogue of [stage
08](../08-serving/) for recommendation. Both are the mission's latency
guardrail made concrete: the p95 budget is a constraint, not
decoration, and in RTB it is the exchange's deadline, not the
platform's own target, that decides whether the bid exists at all.

## Evidence boundary

The executed budget split over six declared stages (illustrative,
deterministic, assumed per-stage latencies). It demonstrates the
allocation; real RTB budgets are measured per stage at p95, and the
timeout cost is the [exchange-timeout detour's](when-the-exchange-times-out/)
arithmetic.

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

**2. What does a timeout do to the auction?**

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
