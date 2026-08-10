# Run — the per-window unit-economics audit over the emitted curves

**Commands:** `uv run python core/unit_economics.py --emit-log /tmp/unit-economics-envelope.json`;
`uv run python prod/unit_economics_audit.py /tmp/unit-economics-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 55's read shows LTV/CAC deciding which channel the platform can
afford. This run is the case-finding half of the stage: LTV/CAC is a
curve over the measured horizon, not a number, and a channel that ramps
slowly looks unaffordable at a short window and dominant at a long one.
The core script emits each channel's 24-month retention curve; the
production audit recomputes LTV/CAC per horizon and checks whether the
window would flip the channel ranking, the way a growth finance team
re-measures unit economics before scaling an acquisition bet.

## Output

```
unit-economics audit (ltv/cac per measured window):
  channel             1m    3m    6m   12m   24m
  organic search     2.50   4.58   6.67   8.77   9.86
  paid installs      0.62   0.88   0.95   0.97   0.97
  referral           0.12   0.78   2.31   5.20  10.02

verdict: WINDOW TRUNCATED -- at 3m the top channel is
'organic search', and at 24m it is 'referral': the window
you measured decides which channel you call the acquisition
bet. Channels that ramp slowly and stay (referral) are
understated at short windows; channels that decay fast (paid
installs) rank above them at short windows and never improve.
Re-measure LTV on the full retention curve, modeled from the
cohort's own recency-frequency data, before scaling spend.
```

## Notes

- The channel ranking flips across the window: organic search tops the
  3m view (4.58) and referral tops the 24m view (10.02); paid installs
  (0.88 at 3m) ranks above referral (0.78) at the short window and never
  improves.
- The audit's message is the stage's: LTV/CAC is a curve, not a number.
  Re-measure on the full retention curve — modeled from the cohort's
  own recency-frequency data, the BG/NBD-style approach (Fader, Hardie &
  Lee, Marketing Science 2005; customer valuation in Gupta, Lehmann &
  Stuart, Journal of Marketing Research 2004) — before scaling spend.
