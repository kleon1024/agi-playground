# Run — competition estimation, the shade measured from censored wins

**Date:** 2026-08-08
**Command:** `uv run python core/competition_estimation.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.4s.
**Cost:** \$0 (local lane).

## Purpose

Stage 39's audit priced a mis-estimated competitor distribution. This
run asks where the estimate comes from: a second-price winner's log
reveals the competitor bid on every win, but a first-price win reveals
nothing, so the bidder must probe win rates with real bids and each
probe is an impression it risks overpaying for. It measures how probe
budget (trials per bid) moves the estimated optimum and the realized
net against the 0.25 the truth allows.

## Output

```
competition unobservable: estimating the shade from censored wins
  value 1.00; truth: competitor uniform on [0, 1]
  second-price reveals the competitor bid on every win;
  first-price reveals nothing, so the bidder probes win rates

probe budget | estimated optimum | realized net | loss vs 0.25
         100 | 0.60              | 0.239      | 0.011
        1000 | 0.50              | 0.249      | 0.001
       10000 | 0.52              | 0.249      | 0.001
      100000 | 0.50              | 0.249      | 0.001

second-price comparison (winner's log reveals competitor bids):
  second-price wins reveal the competitor bid directly;
  10,000 wins estimate P(competitor < 0.50) at 0.5025 against truth 0.5000

reading: the estimate is the bottleneck, and first-price
makes it censored. Every probe bid is an impression the
bidder risks overpaying for, so probing is rationed and the
fitted curve carries noise — at 1,000 trials per probe the
estimated optimum wanders and the realized net loses to the
0.25 truth allows. The trade is probe traffic against
estimation error, and it is the audit's d^2 / 4 loss curve
measured from where the d actually comes from.
```

## Notes

- At 100 trials per probe the fitted win-rate curve is noisy enough
  that the estimated optimum lands at 0.60 instead of 0.50, and the
  realized net loses 0.011 per auction — 4.4 percent of the 0.25 the
  truth allows. Ten times the probes converge the estimate to the
  0.50 optimum (0.249, within Monte Carlo noise).
- The 10,000-row's 0.52 shows the residual wobble: the piecewise
  linear fit over binomial noise can still move the argmax by a cent,
  but the net cost is 0.001, an order of magnitude below the
  100-trials row.
- The second-price contrast is structural, not numeric: every win
  reveals the competitor bid, so the log estimates the distribution
  with no probing at all. First-price removed that free signal, which
  is why bid-landscape estimation became its own industrial problem
  after the 2019 unified-first-price transition (Google Ad Manager).
