---
status: verified
level: applied
base: scratch
label: When the conversion lags
verified: 2026-08-08
---

# A conversion that arrives tomorrow is labeled a negative today

**Question:** [stage 27's bid strategy](../) derives the bid from the
conversion rate. This chapter reads the executed delayed-conversion
audit and asks what happens when the label arrives after the click.

**Before this:** [stage 27 — bid strategy](../) and its executed
value-per-click model, and the recommendation track's
[delayed-feedback stage](../../../recommendation/57-delayed-feedback/)
for the same failure on the recommendation side.

## The snapshot, executed

The run ([record](runs/2026-08-08-delayed-conversion.md)) simulates
100,000 clicks (fixed seed) over a seven-day snapshot with true CVR
0.02 and a lognormal conversion delay (median three days):

| CVR read | CVR | bid (\$5 x CVR) |
|---|---:|---:|
| true | 0.0200 | \$0.10 |
| naive (hard negatives) | 0.0096 | \$0.05 |
| delay-corrected | 0.0197 | \$0.10 |

Naive under-read: 52 percent of the true CVR.

## The failure mode, named

**A conversion that has not arrived yet reads as a negative.** The
conversion label is not available at click time — it arrives after a
delay, so at any snapshot the freshest clicks are the most likely to
still be in flight. A naive model labels them negative because they
have not converted yet, and the audit measures the consequence: CVR
reads 0.0096 against a true 0.02, a 52 percent under-read, and the
target-CPA bid falls from \$0.10 to \$0.05. The under-bid then loses
the auctions the advertiser should have won — the campaign starves
itself of inventory precisely because the label lies.

**The bias concentrates in the traffic that matters most.** Fresh
traffic is the most censored: a click from today has almost no chance
to have converted yet, so its label is almost always a hard negative
even when it will convert. That means the model's worst bias sits on
the newest, most representative traffic — the same young-snapshot
mechanic the recommendation track measures in
[stage 57](../../../recommendation/57-delayed-feedback/), where the naive
model under-reads fresh traffic at 0.092 against a true 0.132. The ads
version is worse in direction: a recommendation model under-reads a
metric, an advertiser under-reads a bid, and the bid loses auctions.

**Waiting for maturity is not an option.** The naive alternative —
train only on clicks old enough to have converted — throws away the
fresh traffic, which is exactly where the campaign's current value is.
The recommendation stage's snapshot arithmetic applies here too: with
a three-day median delay, a one-day-old snapshot has almost no mature
rows at all. The fix must keep the fresh clicks and correct their
labels, not discard them (Chapelle, 2014, KDD, "Modeling delayed
feedback in display advertising": a conversion window of 30 days, and
a delay model that decides whether an unresolved click is treated as a
negative or left out).

## Who owns the loop

- **The conversion-model team** owns the label: the joint conversion-
  and-delay fit, the soft label for in-flight clicks, and the window
  choice. It owns the under-read failure — the audit measured naive
  CVR at 0.0096 against 0.02, with the corrected model recovering
  0.0197 (Chapelle, 2014).
- **The bid strategy team** owns the bid the label feeds: the
  target-CPA derivation, and the auction-loss consequence when the
  estimate underbids. It owns the starved-inventory failure — a bid
  of \$0.05 instead of \$0.10 wins only the cheap tail of the
  auction, so the campaign buys the worst impressions at the worst
  rate.
- **The data and measurement team** owns the snapshot: label maturity
  per age cohort, delay distribution per product and channel, and the
  freshness monitor that tells when the naive read is drifting. It
  owns the invisible-bias failure — a campaign dashboard reading a
  CVR that is half the true rate sees a "low conversion problem"
  where there is a label problem, and nobody owns the delay
  distribution that would have said so.

When the ownership is implicit, the model team fits hard negatives on a
young snapshot, the bid team trusts the number, and the campaign
quietly stops winning auctions — while the report explains the low CVR
with the wrong cause.

## The fix and its trade

The measured fix is the joint conversion-and-delay model: keep every
click and give each not-yet-converted click a soft label equal to the
probability it still converts, estimated from the delay distribution
(Chapelle, 2014, KDD, fits the delay model and treats unresolved clicks
by predicted delay — negative when the elapsed time exceeds it,
excluded when it is too early to tell). The audit's corrected read of
0.0197 against the naive 0.0096 is the payoff, and the bid returns to
\$0.10. The trade is on the window and the delay estimate: a longer
window matures more labels but delays learning (the freshness the
campaign is buying); a wrong delay model misplaces the censoring
boundary and converts a label fix into a new bias. The recommendation
track's stage 57 walks the same window trade — the corrected model
there tracked fresh traffic at 0.142 against a true 0.132 while the
naive read 0.092.

## Evidence boundary

The executed audit uses a declared delay distribution and Bernoulli
conversions over 100,000 synthetic clicks (fixed seed). It
demonstrates the censoring mechanism and the correction; real delay
distributions are estimated per product, channel, and device, and the
window choice is a product decision measured on held-out labels.

## Check your mental model

Answer each before opening it.

**1. Why does a young snapshot under-read CVR?**

<details>
<summary>Answer</summary>

Because the freshest clicks are the most likely to still be in flight.
A click from today has almost no chance to have converted yet, so its
hard label is a negative even when it will convert in two days. The
naive model averages those false negatives into the estimate — the
audit read 0.0096 against a true 0.02, a 52 percent under-read — and
the bias lands on the newest, most representative traffic.

</details>

**2. What does the under-read do to the bid, and why is that worse than
an under-read metric?**

<details>
<summary>Answer</summary>

It underbids: the target-CPA bid falls from \$0.10 to \$0.05, and the
campaign loses the auctions it should have won, winning only the cheap
tail. A recommendation model under-reading a metric misreports
performance; an advertiser under-reading CVR misprices every auction —
the error turns directly into lost inventory and a campaign that looks
like a conversion problem when it is a label problem.

</details>

## Next

Back to [stage 27](../), where the bid is the expected value of a
click. The [target-CPA detour](../when-the-target-cpa-binds/) shows the
walk-away line the bid implements, and the [bid-capped
detour](../when-the-bid-is-capped/) shows the cap that bounds it from
above.
