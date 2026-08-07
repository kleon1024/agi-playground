---
status: verified
level: applied
base: scratch
label: ECPM ranking
verified: 2026-08-07
---

# The ranking shows the low-bid ad first. Is the revenue real?

**Question:** the platform ranks ads by expected revenue — bid times
click probability, scaled to eCPM — and the low bidder wins. That is the
mechanism. The operational symptom is different: revenue is below the
ranking's promise, and the reason is that the ranking runs on estimates.
This stage executes the objective, then audits what the platform
actually earns when pCTR is wrong.

**Before this:** [stage 14 — ad auction](../14-ad-auction/) for the slot
allocation, and [stage 04's fine-rank](../../shared/04-fine-rank/) for the click
estimate.

## The mechanism, executed

The run ([record](runs/2026-08-06-ecpm-ranking.md)) executes the eCPM
ranking:

| ad | bid | pCTR | eCPM |
|---|---:|---:|---:|
| Ad B | 0.50 | 0.30 | 150.00 |
| Ad C | 1.00 | 0.12 | 120.00 |
| Ad A | 2.00 | 0.05 | 100.00 |

ECPM = bid × pCTR × 1000: the expected revenue per thousand impressions.
Ranking by the product means a low bid with a high click rate beats a
high bid with a low one — Ad B wins despite the lowest bid, because its
0.30 pCTR makes each impression worth more. The platform does not earn
bids; it earns clicks, and eCPM is the estimate of what a slot is
actually worth.

## The failure mode, named and audited

**An unchecked estimate hands revenue to the wrong ad.** The audit
([record](runs/2026-08-07-ecpm-rank-error.md)) perturbs each ad's pCTR
by six multipliers, re-ranks by estimated eCPM (ties broken by bid), and
measures realized revenue against the optimal 150.00 per impression:

| perturbation | winner flips | mean realized revenue | mean loss |
|---|---:|---:|---:|
| 18 cells (6 per ad) | 7 (38.9%) | 136.11 | 13.89 |

The symptom is measured: errors large enough to flip the winner cost
30-50 per impression (Ad A's overestimate hands the slot to itself and
loses 50; Ad B's underestimate hands it to Ad C and loses 30), while
half-measure errors that keep the true winner on top cost nothing. The
ranking is only as good as the estimate — and the audit's realized
column is the online check that catches a flip before the revenue
report does.

**The estimate sits on a knife-edge.** The
[when-pctr-moves-the-rank detour](when-pctr-moves-the-rank/) sweeps one
ad's pCTR and finds a 2-point change (0.07 to 0.09) swaps the winner.
The flip point is the tolerance measure: it says how precisely pCTR must
be estimated for the ranking to be trustworthy — and calibration (stage
16) is the precondition that keeps estimates inside the budget.

**When the estimate ties, the rule decides.** The
[when-the-bids-tie detour](when-the-bids-tie/) reads two ads tying at
estimated eCPM 100.00: by-bid and by-quality pick different winners
under true pCTR (realized 100.00 vs 120.00 or 80.00), so the tie-break
rule is a policy choice about incentives, not arithmetic.

**The reserve and the ranking are one decision.** The
[when-the-reserve-interacts detour](when-the-reserve-interacts/) applies
the stage-14 floor to the ranking: at reserve 125 only Ad B (150) is even
eligible, and at 160 the slot shows nothing. The floor filters before the
ranking orders — what the platform refuses to show and the order it shows
are one decision.

## Who owns the loop

The ranking only earns what someone is accountable for at each side of
the revenue loop, and each owner is tied to one of the failure modes
above:

- **The ranking and calibration team** owns the pCTR estimate and the
  ranking key: keeping calibration current (stage 16) and re-auditing
  the ranking's realized column when the model changes. It owns the
  knife-edge failure — the audit measured 38.9 percent of perturbations
  flipping the winner, and calibration is the instrument that keeps
  estimates inside the flip-point budget (Guo, Pleiss, Sun & Weinberger,
  2017, ICML; Naeini, Cooper & Hauskrecht, 2015, AAAI).
- **The pricing and auction team** owns the tie-break rule and the
  reserve: choosing a rule for its incentive properties, not its
  realized column, and setting the floor with the ranking's eCPMs in
  view. It owns the tie and the reserve-interaction failures (Varian,
  2007, *International Journal of Industrial Organization* 25(6):1163-
  1178; Cavallo & Wilkens, 2014, arXiv:1410.3048: tie-breaking changes
  the allocation and is not innocuous).
- **The ads-measurement team** owns realized revenue: reconciling the
  ranking's predicted eCPM against what each slot actually earns, by
  ad and by slice. It owns the invisible-loss failure — a ranking that
  under-delivers without anyone noticing until the audit's realized
  column exposes the flip.

When the ownership is implicit, the model team ships a pCTR update, the
ranking re-orders the pool, and nobody re-checks the realized column —
the revenue decline the stage opened with lands as a mystery instead of
an estimate-tolerance finding.

## Why this belongs in the mission

Mission 02's contract covers ads as a paid placement inside
recommendation and search. Ranking is where the click model and the
auction meet: pCTR is the estimate, eCPM is the objective, and the
realized column is the production loop that ties the model's output to
the platform's revenue. The stage's owner is the ranking team precisely
because the auction (stage 14) exposed the value and this stage decides
who gets it.

## Evidence boundary

The executed mechanism over three hand-built (bid, pCTR) pairs and the
audit's perturbation grid are illustrative and deterministic. They
demonstrate the eCPM objective and the revenue cost of estimate error;
they do not model a real pCTR model's error distribution, multi-slot
position effects, or advertiser response, where realized revenue is
measured from logged outcomes rather than assumed multipliers.

## Check your mental model

Answer each before opening it.

**1. Why is Ad B with the lowest bid the most valuable?**

<details>
<summary>Answer</summary>

Because value is bid times click probability, not bid alone. Ad B's 0.30
pCTR means roughly three in ten impressions earn the platform its bid;
Ad A's 0.05 means one in twenty. Per thousand impressions, B earns 150
against A's 100. The bid reveals intent; the pCTR reveals audience
fit — and eCPM is where the two meet.

</details>

**2. Your ranking says 150 per impression; revenue says 136. Where do
you look?**

<details>
<summary>Answer</summary>

At the realized column of the ranking audit, stratified by ad. The
measured grid lost 13.89 per impression on average because 7 of 18
perturbations flipped the winner — and every flip cost 30-50. A
systematic overestimate on the pool's high-bid ads hands slots to ads
that underperform, and the ranking keeps predicting the revenue it never
earns. The check is realized revenue by ad against predicted eCPM, not
the model's loss on its own training data.

</details>

**3. What breaks if pCTR is wrong?**

<details>
<summary>Answer</summary>

The ranking optimizes against a wrong revenue estimate. An overestimated
pCTR inflates eCPM and wins slots for ads that underperform — the
platform earns less than the ranking predicted, and the auction pays the
wrong price. That is why calibration (stage 16) is not a polish step: it
is the precondition that makes eCPM ranking correct.

</details>

## Next

Forward to [stage 16 — pCTR calibration](../16-ctr-calibration/) which
keeps the estimate honest.

A detour from here: [the knife-edge the click estimate sits on](when-pctr-moves-the-rank/) — the executed sweep read: a 2-point pCTR change swaps the winner, and the stage audit measured 7 of 18 perturbations flipping the rank at a mean cost of 13.89 per impression.

Another detour: [the tie-break rule decides who wins when the estimate cannot](when-the-bids-tie/) — the executed tie read: two ads at estimated eCPM 100.00 realize 100.00 or 120.00/80.00 depending on the rule, so the choice is about incentives, not arithmetic.

A third detour: [the reserve and the ranking are one decision](when-the-reserve-interacts/) — the executed combination read: at reserve 125 only Ad B (150) clears the floor, so what the platform refuses to show and the order it shows are one decision.

## Evidence boundary

The executed ranking over three hand-built (bid, pCTR) pairs
(illustrative, deterministic). It demonstrates the objective; real eCPM
ranking needs a calibrated pCTR model and a reserve price from the
auction stage.

## Check your mental model

Answer each before opening it.

**1. Why is Ad B with the lowest bid the most valuable?**

<details>
<summary>Answer</summary>

Because value is bid times click probability, not bid alone. Ad B's 0.30
pCTR means roughly three in ten impressions earn the platform its bid;
Ad A's 0.05 means one in twenty. Per thousand impressions, B earns 150
against A's 100. The bid reveals intent; the pCTR reveals audience
fit — and eCPM is where the two meet.

</details>

**2. What breaks if pCTR is wrong?**

<details>
<summary>Answer</summary>

The ranking optimizes against a wrong revenue estimate. An overestimated
pCTR inflates eCPM and wins slots for ads that underperform — the
platform earns less than the ranking predicted, and the auction pays the
wrong price. That is why calibration (stage 16) is not a polish step: it
is the precondition that makes eCPM ranking correct.

</details>

## Next

Forward to [stage 16 — pCTR calibration](../16-ctr-calibration/) which
keeps the estimate honest.

A detour from here: [the knife-edge the click estimate sits on](when-pctr-moves-the-rank/) — the executed sweep read: a 2-point pCTR change swaps the winner, which is why calibration is the precondition.

Another detour: [the reserve and the ranking are one decision](when-the-reserve-interacts/) — the executed combination read: at reserve 125 only Ad B (150) clears the floor, so what the platform refuses to show and the order it shows are one decision.
