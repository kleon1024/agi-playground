# Run — LTV and CAC, executed on the unit-economics read

**Date:** 2026-08-07
**Commands:** `uv run python core/unit_economics.py --emit-log /tmp/unit-economics-envelope.json`;
`uv run python prod/unit_economics_audit.py /tmp/unit-economics-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 55 introduces unit economics. This run computes the five-month
lifetime value per user for three acquisition channels, then emits each
channel's full 24-month retention curve for the production audit to
recompute LTV/CAC per measured window.

## Output

```
ltv and cac, read (5-month lifetime value per user):
  organic search  cac $2.00, ltv $12.15, ltv/cac 6.08
  paid installs   cac $8.00, ltv $7.50, ltv/cac 0.94
  referral        cac $4.00, ltv $7.20, ltv/cac 1.80

reading: organic search pays back ~6x its acquisition cost;
paid installs return less than the cost of the user - every
paid signup loses money once retention is counted. A channel
with a low CAC is not a cheap channel if its users leave.
Unit economics decide which growth is real growth.

horizon view (ltv/cac per measured window):
  channel             1m    3m    6m   12m   24m
  organic search     2.50   4.58   6.67   8.77   9.86
  paid installs      0.62   0.88   0.95   0.97   0.97
  referral           0.12   0.78   2.31   5.20  10.02

  reading: referral looks weak at 3 months (0.78) and
  dominant at 24 (10.0) because its users ramp slowly and
  stay; paid installs looks fine at 3 months (0.88) and
  never improves. The window you measure decides which
  channel you call the acquisition bet.
```

## Notes

- Organic search returns 6.08x its CAC; paid installs return 0.94x and lose money once retention is counted.
- A channel with a low CAC is not a cheap channel if its users leave; unit economics decide which growth is real growth.
- The horizon view is the case-finding half of the stage: referral's
  LTV/CAC climbs from 0.78 at 3 months to 10.02 at 24, so the measured
  window decides which channel the platform calls the acquisition bet.
  The audit reads the emitted curves and returns the WINDOW TRUNCATED
  verdict; see the audit record.
