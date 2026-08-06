---
status: verified
level: applied
base: scratch
label: Budget pacing
verified: 2026-08-06
---

# Spend the day, not the first hour

**Question:** an advertiser has a daily budget, and the platform must
deliver it across the day — spend everything in the morning spike and the
campaign is dark when evening demand arrives. This stage simulates naive
versus paced delivery.

**Before this:** [stage 16 — pCTR calibration](../16-ctr-calibration/) for
the click estimate, and [stage 08's serving](../08-serving/) for why
delivery is a runtime constraint.

## The simulation, executed

The run ([record](runs/2026-08-06-budget-pacing.md)) executes delivery
under a front-loaded demand curve (a 100-unit budget, 200 units of
demand):

| hour | naive spend | paced spend |
|---:|---:|---:|
| 0 | 36.3 | 8.3 |
| 1 | 33.2 | 8.3 |
| 2 | 30.2 | 8.3 |
| 3 | 0.3 | 8.3 |
| 4+ | 0.0 | 8.3 → tapers |

Naive exhausts at hour 3; paced survives the day (88.4 of 100 spent).

## The mechanism, named

Pacing caps the per-hour spend at a fraction of the daily budget, so the
campaign delivers continuously instead of exhausting early. Two designs:

1. **Naive (no cap)** — spend on every impression as it arrives. A
   morning spike consumes the budget and the campaign is dark for the
   rest of the day.
2. **Paced (cap per slice)** — limit hourly spend to budget/hours, then
   adjust as actual delivery deviates from the plan.

The executed run shows the consequence: naive is dark at hour 4, paced
still delivers at hour 11.

## Why pacing matters for the platform

An advertiser who spends their budget in one hour gets one hour of
exposure, then nothing — and is less likely to renew. Pacing converts
that into full-day presence, which is better for the advertiser and the
platform's relationship. But pacing has a cost: the cap can leave budget
unspent when demand is low (11.6 unused here), which is why real systems
re-pace — tighten the cap when ahead, loosen when behind — against live
delivery.

## Evidence boundary

The executed simulation over one hand-built front-loaded demand curve
(illustrative, deterministic). It demonstrates the pacing mechanism; real
pacing also models bid price, competition, and the auction's win rate.

## Check your mental model

Answer each before opening it.

**1. Why is exhausting the budget early a failure?**

<details>
<summary>Answer</summary>

Because the budget buys the wrong exposure. Spending 100 in the morning
spike buys impressions at the hour when competition is highest, then the
campaign misses the evening demand entirely — the advertiser paid for a
day of delivery and got an hour. Pacing is not about spending less; it is
about spending at the moments the budget was meant to cover.

</details>

**2. What does the 11.6 unused mean for the pacing design?**

<details>
<summary>Answer</summary>

That a fixed cap is conservative — it protects against overspend but can
leave budget on the table when demand is low. Real pacing is feedback
control: if delivery is behind, loosen the cap; if ahead, tighten it.
The unused budget is the cost of the simple design, and the dynamic
re-pacing is the fix a production system needs.

</details>

## Next

Forward to [stage 18 — ad externality](../18-ad-externality/) where the
ads track returns to the mission's central trade: every ad displaces an
organic result.

A detour from here: [the cap that binds when demand spikes](when-delivery-varies/) — the executed controller read: spend holds flat at the cap while demand triples, and the remaining column is the feedback signal.
