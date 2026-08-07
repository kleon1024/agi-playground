---
status: verified
level: applied
base: scratch
label: ECPM ranking
verified: 2026-08-06
---

# The lowest bid that wins

**Question:** an ad's value to the platform is not its bid — it is the
expected revenue: bid times click probability, scaled to eCPM. This stage
ranks ads by that objective and shows why the highest bidder loses.

**Before this:** [stage 14 — ad auction](../14-ad-auction/) for the slot
allocation, and [stage 04's fine-rank](../../shared/04-fine-rank/) for the click
estimate.

## The ranking, executed

The run ([record](runs/2026-08-06-ecpm-ranking.md)) executes the eCPM
ranking:

| ad | bid | pCTR | eCPM |
|---|---:|---:|---:|
| Ad B | 0.50 | 0.30 | 150.00 |
| Ad C | 1.00 | 0.12 | 120.00 |
| Ad A | 2.00 | 0.05 | 100.00 |

## The mechanism, named

ECPM = bid × pCTR × 1000. Two quantities, multiplied:

1. **The bid** — the advertiser's stated value per click.
2. **pCTR** — the model's estimate of the click probability.

The product is the expected revenue per thousand impressions. Ranking by
it means a low bid with a high click rate can beat a high bid with a low
one — Ad B wins despite the lowest bid, because its 0.30 pCTR makes it
worth more per impression.

## Why ranking by bid is wrong

Ranking by bid alone shows Ad A first — but Ad A's 5% click rate means
each impression earns the platform little. The platform does not earn
bids; it earns clicks (or conversions). eCPM is the estimate of what a
slot is actually worth, which is why it, not the raw bid, is the ranking
key. The pCTR that feeds it must be calibrated (stage 16), or the ranking
is optimized against a wrong number.

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
