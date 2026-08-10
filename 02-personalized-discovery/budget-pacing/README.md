---
status: verified
level: applied
base: scratch
label: Budget pacing
verified: 2026-08-07
---

# The budget is spent, so why is the advertiser's evening dark?

**Question:** an advertiser has a daily budget, and the platform must
deliver it across the day. The mechanism is pacing — cap the spend per
time slice so the campaign survives the morning spike. The operational
symptom is different: the budget is fully spent, yet the campaign is dark
when evening demand arrives. The failure is a cap tuned loose, and the
fix is measured against where the demand actually sits.

**Before this:** [stage 16 — pCTR calibration](../16-ctr-calibration/) for
the click estimate, and [stage 08's serving](../../shared/08-serving/) for why
delivery is a runtime constraint.

## The mechanism, executed

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

Pacing caps the per-hour spend at a fraction of the daily budget, so the
campaign delivers continuously instead of exhausting early. Two designs:

1. **Naive (no cap)** — spend on every impression as it arrives. A
   morning spike consumes the budget and the campaign is dark for the
   rest of the day.
2. **Paced (cap per slice)** — limit hourly spend to budget/hours, then
   adjust as actual delivery deviates from the plan.

<!-- interactive: BudgetPacing -->

## The failure mode, named and audited

**A loose cap spends the budget, then misses the evening.** The audit
([record](runs/2026-08-07-pacing-sweep.md)) sweeps the cap tightness
(multiplier on budget/hours) over a front-loaded demand curve with an
evening burst:

| cap multiplier | total spent | late-window spend (hours 9-11) | dark hours |
|---:|---:|---:|---:|
| 0.50 | 50.0 | 12.5 | 0 |
| 1.00 | 97.3 | 25.0 | 0 |
| 1.25 | 100.0 | 13.0 | 1 |
| 1.50 | 100.0 | 0.0 | 3 |
| 2.00 | 100.0 | 0.0 | 5 |

The symptom is measured: total spend looks healthy at 1.50 (100.0 of
100), but the late-window column collapses to 0.0 with three dark hours —
the advertiser's evening is gone even though the budget is fully spent.
Late-window delivery is the metric that catches the loose cap before the
advertiser does.

**A tight cap under-delivers.** The same sweep at multiplier 0.50 spends
only half the budget: the cap protects against overspend but leaves money
on the table when demand is low. The trade — unspent budget against
missed evening demand — is what cap tuning optimizes, and the answer
depends on the demand shape, which is why the cap is tuned against logged
delivery, not fixed once.

**The feedback controller can oscillate.** The
[when-the-pacer-overcorrects detour](when-the-pacer-overcorrects/)
replaces the fixed cap with a feedback controller and measures the gain
failure: at gain 3.0 the campaign is dark six of twelve hours, flooding
after every deficit and clamping to 0 after every surplus. The variance
detour's fixed cap under-delivers; this is the opposite failure on the
same budget.

**The cap binds exactly when demand spikes.** The
[when-delivery-varies detour](when-delivery-varies/) runs the fixed cap
against demand that triples and measures the cap holding spend flat while
demand spikes — the remaining column is the feedback signal a production
controller consumes.

**Pacing cannot create a budget.** The
[when-the-budget-is-tiny detour](when-the-budget-is-tiny/) runs the same
controller at budgets 100, 20, and 8: at 8 the cap falls below the
minimum viable spend and the campaign barely delivers — the floor is a
sizing decision, not a pacing one.

## The fix and its trade

The fix is feedback control: re-pace the cap against live delivery
instead of fixing it once, because the failure the audit names is the cap
tuned loose, not pacing itself. The sweep prices the repair — at
multiplier 1.50 the budget spends fully (100.0 of 100) but late-window
delivery collapses to 0.0 with three dark hours, so the campaign is
measured by late-window delivery and the dark-hour count, not total
spend, and the controller tightens the cap before the evening burst.

The trade is that the controller has its own failure modes and cannot
create a budget. A tight cap protects against overspend but leaves money
on the table: multiplier 0.50 spends only 50.0 of 100. Feedback gain can
oscillate — at gain 3.0 the campaign is dark six of twelve hours, flooding
after every deficit and clamping to 0 after every surplus — and at budget
8 the cap falls to 1/hour, where no pacing can deliver. The cap is tuned
against logged delivery, and the answer depends on the demand shape,
which the measurement team owns.

## Who owns the loop

The budget only delivers what someone is accountable for at each side of
the pacing loop, and each owner is tied to one of the failure modes
above:

- **The delivery and pacing team** owns the controller: the cap, the
  feedback gain, and the re-pacing against live delivery. It owns the
  oscillation and tight-cap failures — the audit measured 6 dark hours
  at gain 3.0 and 50.0 of 100 unspent at multiplier 0.50 (Agarwal,
  Ghosh, Wei & You, 2014, KDD: delivery-rate pacing at LinkedIn; Xu et
  al., 2015, KDD: smart pacing as a delivery optimization at Yahoo).
- **The campaign-management team** owns the budget and the targeting:
  sizing the budget above the minimum viable spend and shaping the
  audience so the cap buys meaningful delivery. It owns the tiny-budget
  failure — at budget 8 the cap is 1/hour and no pacing can fix it
  (Zhang, Yuan & Wang, 2014, KDD: optimal real-time bidding; Wang, Zhang
  & Yuan, 2017, *Foundations and Trends in Information Retrieval*
  11(4-5): bidding and pacing as one delivery-control problem).
- **The ads-measurement team** owns delivery monitoring: total spend by
  time-of-day slice, late-window delivery, and the dark-hour count. It
  owns the spends-but-misses failure — the difference between the 100.0
  total at multiplier 1.50 and its 0.0 late-window delivery is its
  standing check.

When the ownership is implicit, the pacing team tunes the cap against a
demand shape the campaign team never states, and the measurement team
reports a full spend nobody attributes to dark hours — the symptom the
stage opened with.

## Why this belongs in the mission

Mission 02's contract covers ads as a paid placement inside
recommendation and search. Pacing is where the platform's delivery
promise meets the advertiser's budget: the auction prices the impression
(stage 14), the ranking picks it (stage 15), and pacing decides whether
the budget buys the day it promised. The stage's owner is the delivery
team because the failure is a distribution-over-time problem, not a
model problem.

## Evidence boundary

The executed simulation and audits use hand-built demand curves and cap
sweeps with no random draws (illustrative, deterministic). They
demonstrate the pacing mechanism and the cap-tightness trade; they do not
model bid price, competition, the auction's win rate, or measurement lag,
where the optimal cap is derived from logged auction outcomes rather
than assumed.

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

**2. The budget is fully spent and the advertiser complains the evening
was dark. Where do you look?**

<details>
<summary>Answer</summary>

At the delivery time-of-day distribution, before the total. The audit
measured a fully-spent budget with three to five dark hours at cap
multipliers 1.50-2.00 — the total hid the collapse. The late-window
delivery column is the check: when it drops while total spend holds, the
cap is loose relative to the demand shape, and the fix is to tighten the
cap and shift delivery toward the evening, not to spend more.

</details>

**3. What does the 11.6 unused mean for the pacing design?**

<details>
<summary>Answer</summary>

That a fixed cap is conservative — it protects against overspend but can
leave budget on the table when demand is low. Real pacing is feedback
control: if delivery is behind, loosen the cap; if ahead, tighten it.
The unused budget is the cost of the simple design, and the dynamic
re-pacing is the fix a production system needs — with the caveat the
overcorrection detour measures, that the feedback gain must stay below
the point where the controller oscillates.

</details>

## Next

Forward to [stage 18 — ad externality](../18-ad-externality/) where the
ads track returns to the mission's central trade: every ad displaces an
organic result.

A detour from here: [the pacer that fixes delivery by oscillating](when-the-pacer-overcorrects/) — the executed controller read: gain 3.0 darkens six of twelve hours while spending the full budget, the feedback failure on top of a fixed cap.

Another detour: [the cap that binds when demand spikes](when-delivery-varies/) — the executed controller read: spend holds flat at the cap while demand triples, and the remaining column is the feedback signal.

A third detour: [pacing cannot create a budget](when-the-budget-is-tiny/) — the executed tiny-budget run read: at budget 8 the cap is 1/hour and the campaign barely delivers, so the floor is a sizing problem, not a pacing one.
