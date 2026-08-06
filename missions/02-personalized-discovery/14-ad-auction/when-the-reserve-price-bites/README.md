---
status: verified
level: applied
base: scratch
label: When the reserve price bites
verified: 2026-08-06
---

# The floor that can also kill the sale

**Question:** [stage 14's ad auction](../) showed the one-bidder case pays
the platform zero. This chapter reads the executed reserve-price sweep
and asks what the floor actually trades.

**Before this:** [stage 14 — ad auction](../) and its executed mechanism.

## The sweep, executed

The run ([record](runs/2026-08-06-reserve-read.md)) sweeps the reserve on
bids [1.00, 0.80]:

| reserve | winner pays |
|---:|---:|
| 0.00 | 0.80 |
| 0.70 | 0.80 |
| 0.85 | 0.85 |
| 0.95 | 0.95 |

## Two readings

**The reserve floors revenue and can kill a sale.** At reserve 0 the
second-price auction pays 0.80; at 0.85 the second bidder is out and the
winner pays the reserve; the floor has turned a competitive price into
the minimum. If the reserve were above the top bid, the slot would go
unsold — the reserve is a real trade between revenue floor and lost
sales.

**The reserve is part of the auction design, not an add-on.** The
one-bidder case made the gap visible: no competition, zero payment. The
reserve is the platform's minimum acceptable price, set per slot or per
context. It interacts with eCPM ranking (stage 15): the reserve decides
whether a low-eCPM ad is worth showing at all, and the auction decides
what it pays.

## Evidence boundary

The executed sweep over one bid set (illustrative, deterministic). It
demonstrates the mechanism; real reserve optimization uses the demand
distribution to balance fill and revenue.

## Check your mental model

Answer each before opening it.

**1. Why does the winner pay the reserve when the second bidder is
eliminated?**

<details>
<summary>Answer</summary>

Because the second-price rule's price is the second-highest *eligible*
bid — and the reserve makes bids below it ineligible. At reserve 0.85,
the 0.80 bidder cannot compete, so the 1.00 bidder faces no valid second
bid and pays the reserve instead. The reserve is the platform standing
in as the minimum competitor.

</details>

**2. What would a reserve above the top bid do?**

<details>
<summary>Answer</summary>

Leave the slot unsold — no eligible bidder clears the floor. That is the
trade's cost side: a high reserve guarantees revenue when a sale happens
but risks no sale at all. Production reserve setting weighs the expected
revenue of a sale at the reserve against the probability of no sale,
which is why it is an economic decision, not a constant.

</details>

## Next

Back to [stage 14](../), or to
[stage 15 — eCPM ranking](../../15-ecpm-ranking/) where the bid meets the
click estimate.
