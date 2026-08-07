# Run — auction revenue, executed on the first-vs-second-price model

**Date:** 2026-08-07
**Command:** `uv run python core/first_vs_second.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 28 asks how the auction rule moves platform revenue. This run
executes the same bids under first- and second-price rules and reads
the gap.

## Output

```
first vs second price, read (bids [1.20, 1.00, 0.80]):
  first price:  winner pays $1.20
  second price: winner pays $1.00

reading: the same auction pays the platform 20 cents more under
first price — but advertisers know that and shade their bids,
which is why the honest-bidding property of stage 14 matters.
Revenue per auction is only half the question; bidder behavior
under the rule is the other half.
```

## Notes

- The identical bids pay the platform \$1.20 under first price and
  \$1.00 under second — a 20-cent gap per auction.
- The gap is not free revenue: bidders anticipate the rule and shade,
  which the when-first-price-pays-more detour executes.
