---
status: verified
level: applied
base: scratch
label: Bid strategy
verified: 2026-08-07
---

# The bidder that trusts its own winner's log overpays for every auction it wins

**Question:** [stage 14's auction](../14-ad-auction/) decides the price
once bids exist. This stage asks where a bid comes from, and answers:
the advertiser bids the expected value of a click — value times
conversion rate — and the audit shows the conversion rate itself is a
biased read unless the bidder corrects for what it can and cannot see.

**Before this:** [stage 14 — ad auction](../14-ad-auction/) for the
mechanism bids enter, and [stage 16 — CTR calibration](../16-ctr-calibration/)
for the estimate the bid inherits.

## The bid, executed

The run ([record](runs/2026-08-07-bid-strategy.md)) derives the bid
from declared advertiser inputs:

| input | value |
|---|---:|
| target CPA | \$5 |
| conversion rate | 2% |
| value per click | \$0.10 |
| target CPA bid | \$0.10 |

A target-CPA bid is value times conversion rate. The advertiser values
a conversion at \$5, expects 2% of clicks to convert, so each click is
worth \$0.10 — and that is the bid. Two properties fall out:

1. **The bid changes with the estimate.** If the conversion rate is
   wrong, the bid is wrong, which is why calibration (stage 16) is the
   advertiser's problem too.
2. **The bid is a walk-away line.** When the auction price passes the
   click's value, the advertiser stops bidding — the
   [target-CPA detour](when-the-target-cpa-binds/) executes that
   refusal.

## The failure mode, named and audited

**The winner's log is a biased sample.** The audit
([record](runs/2026-08-08-cvr-bias.md)) runs 100,000 auctions (fixed
seed) where 90 percent of impressions convert at 0.012 and 10 percent
at 0.08, and the bidder wins where its bid — its conversion estimate —
was high:

| CVR read | CVR | bid (\$5 x CVR) |
|---|---:|---:|
| true (all auctions) | 0.0188 | \$0.09 |
| naive (won auctions) | 0.0316 | \$0.16 |
| IPW-corrected | 0.0187 | \$0.09 |

The verdict is measured: the bidder only logs the 35,672 auctions it
won, and it won them because its estimate — hence its bid — was high.
Those impressions convert better than the market, so the naive CVR
from the winner's log reads 0.0316 against a true 0.0188, and the
target-CPA bid overpays 1.68x for every auction it actually wins. The
inverse-propensity correction, weighting each won observation by the
inverse of its win probability, recovers 0.0187 and the \$0.09 bid —
the fix is a selection correction or a CVR model fit on the full
impression space, not just wins.

**The label that has not arrived yet reads as a negative.** The
[conversion-lags detour](when-the-conversion-lags/) simulates 100,000
clicks with a three-day median conversion delay: the naive model
labels in-flight clicks as negatives and reads CVR at 0.0096 against a
true 0.02 — a 52 percent under-read — and the bid falls from \$0.10 to
\$0.05, losing the auctions the campaign should have won. The
delay-corrected soft label recovers 0.0197 (Chapelle, 2014, KDD,
"Modeling delayed feedback in display advertising": the joint fit of
conversion and delay, treating an unresolved click by its predicted
delay). The same failure family appears on the recommendation side in
[stage 57](../../recommendation/57-delayed-feedback/), where a young
snapshot under-reads fresh traffic.

**The bid is a walk-away line, and a cap is a risk dial.** The
[target-CPA detour](when-the-target-cpa-binds/) shows the refusal: at
\$0.14 against a \$0.10 click value the advertiser stands down, because
a win at that price is a loss. The [bid-capped detour](when-the-bid-is-capped/)
shows the cap's other edge: lowering the cap from \$0.10 to \$0.06
drops wins from 3/5 to 1/5, trading reach for lower average price.

## The fix and its trade

The fix is a selection correction — inverse-propensity weighting on won
auctions, or a CVR model fit on the full impression space — because the
winner's log is the auction's winning half, not its population. The
audit prices the repair: naive CVR from the log reads 0.0316 against a
true 0.0188 and the target-CPA bid overpays 1.68x, while the IPW
correction recovers 0.0187 and the \$0.09 bid. The delay side of the
same family is fixed by the joint conversion-and-delay fit: naive labels
in-flight clicks as negatives and reads 0.0096 against a true 0.02 — a
52 percent under-read — where the delay-corrected label recovers 0.0197.

The trade is that the corrections cost data, and the cap is a risk dial
on top. IPW needs a win-probability model or losing auctions in the log;
delay modeling needs the delay distribution per channel, and both drift
as the funnel changes, so the estimator is a standing artifact with a
re-check. A cap that trades reach for price remains a campaign decision:
lowering the cap from \$0.10 to \$0.06 drops wins from 3 of 5 to 1 of 5,
which is a choice about how many auctions to win, not a correction for
the bias.

## Who owns the loop

The bid only earns what someone is accountable for at each side of the
loop, and each owner is tied to one of the failure modes above:

- **The conversion-model team** owns the CVR estimate: the training
  sample (full impression space, not wins), the selection correction,
  and the joint conversion-and-delay fit for in-flight clicks. It owns
  the winner's-log and under-read failures — the audit measured naive
  CVR 0.0316 against true 0.0188 and naive 0.0096 against true 0.02,
  with both corrections recovering the truth (Chapelle, 2014, KDD).
- **The bid-strategy team** owns the bid: the target-CPA derivation,
  the walk-away line, and the cap. It owns the overpay and starve
  failures — a bid from the winner's log pays 1.68x, a bid from a
  young snapshot wins nothing.
- **The data and measurement team** owns the logs the estimate is fit
  on: win records joined to impressions, label maturity per age
  cohort, and the delay distribution per channel. It owns the
  invisible-bias failure — a log without its losing auctions and a
  snapshot without mature labels both look like data, and both lie in
  opposite directions.

When the ownership is implicit, the model team fits CVR on won logs,
the bid team trusts the number, and the campaign pays \$0.16 for
auctions worth \$0.09 — or, on the young-snapshot side, bids \$0.05
and stops winning at all.

## Why this belongs in the mission

The mission's ads track ran the platform's side of the auction. This
stage completes the loop by deriving the advertiser's side: the bid is
the value signal the auction needs, and the conversion rate is where
the advertiser's model meets its own data. The audit adds the
industrial detail: both failure modes are the same phenomenon — the
bidder's training distribution differs from the distribution it
actually faces — and the corrections (selection weighting, delay
modeling) are the same discipline as calibration, applied to the
advertiser's estimate instead of the platform's.

## Evidence boundary

The executed derivation and the two audits (100,000 synthetic auctions
and clicks, fixed seeds, declared propensities and delays) are
illustrative and deterministic. They demonstrate the bias and its
corrections; real CVR bias is diagnosed by comparing won- versus
full-impression logs and label-maturity cohorts, and the corrections
are fit on logged data with confidence bounds rather than single
tables.

## Check your mental model

Answer each before opening it.

**1. Why does the bid depend on the conversion estimate?**

<details>
<summary>Answer</summary>

Because the advertiser pays per click but values conversions. A click
is worth value times conversion rate, so an error in the conversion
estimate is an error in the bid. That is why calibration is shared:
the platform's pCTR and the advertiser's CVR both feed the same
economic decision.

</details>

**2. Your bidder's conversion rate looks great in its own reports, but
the campaign loses money. Where do you look?**

<details>
<summary>Answer</summary>

At the sample the rate was fit on. A bidder that only logs its wins
measures the impressions where its estimate was high — the audit read
0.0316 there against a true 0.0188, a 1.68x overbid. Compare the won
log against the full impression space, or weight wins by inverse win
probability, before trusting the number that prices every auction.

</details>

**3. What does a fresh-traffic conversion dip tell you?**

<details>
<summary>Answer</summary>

Check the labels before the users. Fresh clicks carry the most
in-flight mass: a conversion that arrives tomorrow is labeled a
negative today, and the audit measured the result — CVR read at
0.0096 against a true 0.02, the bid halved to \$0.05. The dip is the
delay distribution's censoring, not a change in the users, and the fix
is the joint conversion-and-delay model (Chapelle, 2014), not a
marketing response.

</details>

## Next

Forward to [stage 28 — auction revenue](../28-auction-revenue/) where
the payment rule, not just the bids, moves the money.

A detour from here: [the target CPA is a walk-away
line](when-the-target-cpa-binds/) — the executed refusal read: against
a \$0.10/click value the advertiser bids at \$0.06 and \$0.10 and
stands down at \$0.14 and \$0.20, because a win at that price is a
loss.

Another detour: [the cap is a risk dial, not a
price](when-the-bid-is-capped/) — the executed sweep read: lowering the
cap from \$0.10 to \$0.06 drops wins from 3/5 to 1/5 and spend from
\$0.30 to \$0.06, trading reach for lower average price.

A third detour: [a conversion that arrives tomorrow is labeled a
negative today](when-the-conversion-lags/) — the executed snapshot
read: with a three-day median conversion delay, the naive model reads
CVR at 0.0096 against a true 0.02 and the bid falls from \$0.10 to
\$0.05, so the delay-corrected soft label is the bid's precondition.
