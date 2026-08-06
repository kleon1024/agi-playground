# Run — the ad externality, executed on the stage's displacement model

**Date:** 2026-08-06
**Command:** `uv run python core/ad_externality.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

The mission's contract states the defining feature: every ad displaces an
organic result. This run quantifies the displacement — the organic value
lost per ad shown.

## Output

```
  1 ad(s): organic kept [0.9, 0.8, 0.7, 0.5] (sum 2.9), displaced 0.3, ad value 0.6
  2 ad(s): organic kept [0.9, 0.8, 0.7] (sum 2.4), displaced 0.8, ad value 1.2
  3 ad(s): organic kept [0.9, 0.8] (sum 1.7), displaced 1.5, ad value 1.8
```

## Notes

- The ad's net value is its revenue minus the organic value it displaced.
- Two ads displace 0.8 of organic for 1.2 of ad value — the trade is
  real, and the value tree (stage 05) is where the platform decides how
  much organic it may displace.
