# Run — when the retention window truncates, executed on the window read

**Date:** 2026-08-07
**Command:** `uv run python core/retention_window.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 55's detour: LTV is measured on an observation window, and the
window truncates the cohort's curve. This run compares each channel's
3-month observed LTV against its true 24-month value, and reads the
verdict flip.

## Output

```
retention window truncates, read (24-month ltv, $5/month):
  channel         3-month view  true 24m 3m ltv/cac true ltv/cac
  paid installs   $      7.05 $    7.78       0.88         0.97
  referral        $      3.10 $   47.10       0.78        11.78

reading: at three months paid installs looks like the better
bet (0.88 vs 0.78) - its curve is fully visible because it
decays immediately. Referral looks weak because its users
ramp slowly; the truncated window sees only the ramp, not the
flat 0.42 tail, so the 3-month ltv/cac is 0.78 against a true
11.8. A team that reads the window and stops ranks the wrong
channel; the fix is to model the curve from recency-frequency
data instead of reading the truncated window as the truth.
```

## Notes

- At three months paid installs (0.88) looks better than referral
  (0.78); at twenty-four months referral is 11.78 against paid's 0.97 —
  the window decides which channel the review promotes.
- The fix is to model the retention curve from recency-frequency data
  (Fader, Hardie & Lee, Marketing Science 2005) and to report LTV/CAC
  per horizon before scaling spend (Gupta, Lehmann & Stuart, Journal of
  Marketing Research 2004).
