---
status: verified
level: applied
base: scratch
label: When the demand curve is elastic
verified: 2026-08-08
---

# The cut chases both sides away, and the peak falls

**Question:** [stage 42's marketplace economics](../) prices the take
rate against one volume-response curve. This chapter reads the
executed two-sided sweep and asks the failure mode that curve skips:
the side that does not pay still responds — raising the cut chases
sellers away, the thinner selection chases buyers away, and the revenue
peak is lower than the one-sided curve promises.

**Before this:** [stage 42 — marketplace economics](../) and its
executed one-sided take-rate model.

## The two-sided model, executed

The run ([record](runs/2026-08-08-two-sided-feedback.md)) keeps the
stage's exact seller price sensitivity and adds the cross-side
response: buyers shrink with the selection (`buyers = sellers`), and
transactions are the matches between the two sides:

| rate | one-sided volume | two-sided volume | two-sided revenue |
|---|---:|---:|---:|
| 5% | 920 | 846 | \$42.3 |
| 15% | 760 | 578 | \$86.6 |
| 25% | 600 | 360 | \$90.0 |
| 35% | 440 | 194 | \$67.8 |
| 45% | 280 | 78 | \$35.3 |

The one-sided revenue peak is 31.0% / \$156.2; the two-sided peak is
21.0% / \$92.6. Pricing at the one-sided optimum (31.0%) once the
cross-side feedback is included earns \$78.7, 15.0% below the two-sided
peak.

## The failure mode, named and audited

**Pricing the cut as one-sided when the market is two-sided.** Stage
42's executed curve treats volume as a function of the rate alone, as
if only the paying side responds. A marketplace does not work that
way: sellers and buyers are complements, and each side's willingness
to transact depends on the size and quality of the other (Rysman 2009,
"The Economics of Two-Sided Markets", Journal of Economic Perspectives
23(3):125-143, doi 10.1257/jep.23.3.125). When the fee rises, sellers
leave first; the thinner marketplace is worth less to buyers; buyers
leave too; and transactions fall twice over. The amplification is
visible at every row — at 35% the one-sided curve keeps 440
transactions, the two-sided model only 194 — and the peak falls from
31.0% to 21.0%.

**The optimum shifts because the fee prices both sides.** The
one-sided peak ignores the demand it destroys on the non-paying side;
the two-sided peak is lower because the marginal fee costs a
transaction on each side — the seller it prices out and the buyers
that seller's presence kept. The profit-maximizing price is set by the
interaction of both sides' elasticities, not either one alone (Rochet
and Tirole 2003, "Platform Competition in Two-Sided Markets", Journal
of the European Economic Association 1(4):990-1029), and Weyl (2010,
"A Price Theory of Multi-sided Platforms", American Economic Review
100(4):1642-1672) shows that price can sit above or below what either
side's own demand curve suggests: the platform prices the bundle, not
the side.

**The blind spot is a measurement problem, not a model choice.** Both
models start at 1,000 transactions and use the same seller sensitivity;
the difference is only that the two-sided model asks what the
non-paying side does when selection changes. A take-rate decision that
estimates only the paying side's volume response prices the market as
if the other side were a constant. The reserve and the ad load change
what the non-paying side experiences too; the externality detour and
this one are the same decision seen from different sides.

## The fix and its trade

The fix is to price the take rate against the measured cross-side
response, not the paying side's curve alone: estimate both sides'
elasticities, feed the selection externality into the volume model,
and set the rate at the two-sided peak. The trade is that the two-sided
estimate is much harder to get: the cross-side response needs matched
experiments that move one side and measure the other, slower and more
expensive than a simple volume-response curve, and the optimum can sit
so far from intuition that the platform must defend a lower rate to
stakeholders who only see the per-transaction cut. The executed model
sets `buyers = sellers` as a declared simplification; real markets have
asymmetric cross-side strengths, and measuring the actual strength is
what separates a price from a guess.

## Evidence boundary

The executed two-sided model over declared response functions
(illustrative, deterministic, assumed cross-side strength). It
demonstrates the mechanism; real take-rate decisions need measured
elasticities on both sides and the actual cross-side response, which
only a live marketplace provides. The Rysman, Rochet and Tirole, and
Weyl findings are attributed as published.

## Check your mental model

Answer each before opening it.

**1. Why does the peak fall when the two-sided response is added?**

<details>
<summary>Answer</summary>

Because the non-paying side responds too: sellers leave, the thinner
selection shrinks buyers, and transactions fall twice over. The
marginal fee costs more than the one-sided curve charges it with, so
the profit-maximizing rate drops from 31.0% to 21.0%.

</details>

**2. Why is the take rate a two-sided price even when only sellers pay
it?**

<details>
<summary>Answer</summary>

Because buyers respond to the selection, not the fee. When the fee
drives sellers away, buyers experience a worse marketplace and
transact less, so the seller-side fee is paid in buyer-side volume:
the cut prices both sides even when only one writes the check.

</details>

**3. How does this connect to the reserve and the ad load?**

<details>
<summary>Answer</summary>

All three levers change what the non-paying side experiences, and each
looks one-sided when measured on a single curve. The fix is the same
everywhere: measure the side that does not pay.

</details>

## Next

Back to [stage 42](../). The
[take-rate detour](../when-the-take-rate-is-too-high/) reads the
collapse past the peak, and the
[ad-load detour](../when-the-ad-load-moves/) shows the same two-sided
trade on the page: how many ads a marketplace carries.
