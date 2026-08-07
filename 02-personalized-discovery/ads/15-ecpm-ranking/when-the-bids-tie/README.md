---
status: verified
level: applied
base: scratch
label: When the bids tie
verified: 2026-08-07
---

# The tie-break rule decides who wins when the estimate cannot

**Question:** [stage 15's ranking](../) orders ads by estimated eCPM.
When two ads tie on the estimate, the rule that breaks the tie picks the
winner — and true pCTR decides what the slot actually earns. This chapter
reads the executed tie-break audit and asks which rule the platform
should own.

**Before this:** [stage 15 — eCPM ranking](../) and its rank-error audit.

## The tie, executed

The run ([record](runs/2026-08-07-tie-break.md)) places two ads at an
estimated-eCPM tie of 100.00 under a conservative and a generous
estimate, and reports realized revenue under each tie-break rule:

| scenario | by bid (realized) | by quality score (realized) |
|---|---:|---:|
| conservative estimate (true pCTR 0.12) | Ad A, 100.00 | Ad X, 120.00 |
| generous estimate (true pCTR 0.08) | Ad A, 100.00 | Ad X, 80.00 |

## Two readings

**The estimate cannot separate them, so a rule must.** Both ads show
eCPM 100.00; the ranking has no number to decide on. Whatever rule runs
next — higher bid, higher quality score, random — it is making the call
the estimate could not, and its cost shows up only under truth. The
stage audit's flip (38.9 percent of perturbations change the winner) is
the same knife-edge at a finer scale: a tie is the degenerate case.

**The rule is a policy choice, not an arithmetic one.** By-bid keeps the
advertiser's bid a price-taking statement: in the second-price auction
truth is dominant (Vickrey, 1961, *Journal of Finance*), and in the
position-auction work the equilibria line bids up by value, which is why
the bid remains the advertiser's own signal (Varian, 2007,
*International Journal of Industrial Organization*; Edelman, Ostrovsky
& Schwarz, 2007, *American Economic Review*). Tie-breaking by quality
score makes the winner a function of the pCTR model — and the pCTR model
is owned by the platform, not the advertiser, so a bidder who can shift
the estimate can win ties without raising the bid.

## The fix and its trade

The measured fix is to make the tie-break rule explicit, stable, and
revenue-accountable. Log every tie with the rule that broke it and the
realized revenue, then audit the rule's realized column the way this
chapter does (Cavallo & Wilkens, 2014, arXiv:1410.3048, show generalized
second-price tie-breaking changes the allocation and is sensitive to
which side of the tie is favored). The trade is the one the executed
table shows: by-quality can realize +20 when the estimate is
conservative and -20 when it is generous, so the rule wins one error
pattern and loses the other. Production picks the rule for its incentive
properties, then measures the realized column to confirm the allocation
matches the objective.

## Evidence boundary

The executed scenarios are two hand-built (bid, pCTR) pairs with no
random draws (illustrative, deterministic). They demonstrate that the
rule, not the estimate, decides a tie's winner; they do not model
advertiser response, where a by-quality rule creates a bidding
incentive that this read only names.

## Check your mental model

Answer each before opening it.

**1. Why are both rules revenue-neutral until the slot runs?**

<details>
<summary>Answer</summary>

Because the ranking sees only estimates. Both ads show eCPM 100.00, so
either winner looks identical to the ranker. The divergence is entirely
in the realized column — what true pCTR earns from the chosen ad. That is
why tie-break audits must be measured after the fact, on realized
revenue, not judged from the estimate table.

</details>

**2. Which rule would you pick, and what do you give up?**

<details>
<summary>Answer</summary>

By-bid, because it preserves the price-taking incentive: the advertiser
expresses value through the bid and has no channel to influence the
winner except raising it. What you give up is the +20 the executed
conservative scenario shows by-quality can earn when the estimate
under-predicts — and you accept that the pCTR model stays honest, which
is worth more than any single tie's realized revenue.

</details>

## Next

Back to [stage 15](../), or to
[stage 16 — pCTR calibration](../../16-ctr-calibration/) which keeps the
estimate honest enough that ties stay rare.
