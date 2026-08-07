# Run — bid strategy, executed on the target-CPA model

**Date:** 2026-08-07
**Command:** `uv run python core/bid_calc.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 27 asks what an advertiser's bid is. This run computes the value
per click from a target CPA and conversion rate and reads the bid.

## Output

```
bid strategy, read (target CPA $5, CVR 2%):
  value per click: $0.10
  target CPA bid:  $0.10

reading: the advertiser bids the expected value of a click.
A target-CPA bid is value x conversion rate — the bid changes
with the estimate, which is why calibration (stage 16) is the
advertiser's problem too, not just the platform's.
```

## Notes

- With a \$5 target CPA and 2% conversion, the click is worth \$0.10,
  and the advertiser bids exactly that.
- The bid inherits the conversion estimate's error, which is why
  calibration (stage 16) is the advertiser's problem too.
