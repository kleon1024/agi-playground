# Run — when the target CPA binds, executed on the walk-away model

**Date:** 2026-08-07
**Command:** `uv run python core/cpa_binds.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 27 bids to a target CPA. This run reads when the auction price
passes the click's value and the advertiser stands down.

## Output

```
target CPA binds, read (max bid $0.10/click):
  price $0.06: bid
  price $0.10: bid
  price $0.14: stand down
  price $0.20: stand down

reading: when the auction price passes the click's value, the
advertiser stops bidding — a win at that price is a loss. The
target CPA is a walk-away line: the bid protects the budget by
refusing the auctions that would break it.
```

## Notes

- At \$0.06 and \$0.10 the advertiser bids; at \$0.14 and \$0.20 it
  stands down, because a win at that price is a loss.
- The target CPA is a walk-away line that protects the budget by
  refusing the auctions that would break it.
