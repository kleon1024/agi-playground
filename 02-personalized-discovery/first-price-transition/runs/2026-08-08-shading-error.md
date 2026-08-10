# Run — shading error, the estimate decides the net

**Date:** 2026-08-08
**Command:** `uv run python core/shading_error.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.1s.
**Cost:** \$0 (local lane).

## Purpose

Stage 39's shading sweep assumed a uniform competitor on [0, 1] and
found the optimum at half the value. This run asks the industrial
question that sweep skips: the competitor distribution is
unobservable, so the bidder shades against a belief, and the belief
can be wrong. It measures what a mis-estimated competitor distribution
costs — the bidder keeps bidding its believed-optimum 0.50 while the
true competition shifts, and the realized net is compared with the
optimum under the true distribution.

## Output

```
shading error, audited: does the estimate decide the net?
  value 1.00; the bidder believes competitors are uniform on [0, 1] and bids 0.50
  Monte Carlo: 200000 sessions per world, fixed seed

mis-specified world | win | realized net | optimal bid | optimal net | loss
  U[0.0, 1.0]        | 0.50 |     0.250 |      0.50 |     0.250 | -0.000
  U[0.3, 1.3]        | 0.20 |     0.100 |      0.65 |     0.122 | 0.022
  U[0.0, 0.4]        | 1.00 |     0.500 |      0.40 |     0.600 | 0.100

belief-error sweep (truth U[d, 1+d], bidder still bids 0.50):
  d    | win | realized net | optimal bid | optimal net | loss
   -0.3 | 0.80 |     0.400 |      0.35 |     0.422 | 0.023
   -0.1 | 0.60 |     0.300 |      0.45 |     0.303 | 0.002
   +0.0 | 0.50 |     0.250 |      0.50 |     0.250 | -0.000
   +0.1 | 0.40 |     0.201 |      0.55 |     0.203 | 0.002
   +0.3 | 0.20 |     0.100 |      0.65 |     0.122 | 0.022

reading: the loss is the square of the belief error divided
by four — a belief error of 0.3 costs 0.0225 per auction,
9 percent of the stage's optimal net of 0.25. Under-shading
against stronger competition loses wins (win 0.20);
over-shading against weaker competition wins everything but
overpays (win 1.00, net 0.50 against an optimum of 0.60).
The competitor distribution is unobservable, so the shade is
an estimate and the estimate's error lands directly in net
value (Google moved Ad Manager to unified first price in
2019; Vickrey 1961, J. Finance; Edelman, Ostrovsky &
Schwarz 2007, AER; Varian 2007, IJIO).
```

## Notes

- The loss is the square of the belief error divided by four: a belief
  error of 0.3 costs 0.022 per auction, 9 percent of the stage's
  optimal net of 0.25 (the sweep shows 0.022 and 0.023, matching
  d-squared-over-four plus Monte Carlo rounding).
- Direction matters, not just magnitude. Under-shading against
  stronger competition (truth U[0.3, 1.3]) wins only 20 percent of
  auctions; over-shading against weaker competition (truth U[0, 0.4])
  wins everything but nets 0.50 against an optimum of 0.60. The belief
  error is a direct cost in net value either way.
- The bidder in first price never sees the competitor's bid — a win
  reveals only its own payment — so the distribution is estimated, and
  this run prices the estimate's error. The competition-unobservable
  detour measures where the estimate itself comes from.
