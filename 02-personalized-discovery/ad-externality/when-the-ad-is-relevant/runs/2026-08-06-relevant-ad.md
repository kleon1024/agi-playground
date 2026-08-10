# Run — when the ad is relevant, executed on the sign flip

**Date:** 2026-08-06
**Command:** `uv run python core/relevant_ad.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Stage 18 shows ads displacing organic value. This run shows the
subtlety: a relevant ad may be worth more than what it displaces.

## Output

```
  ad user value 0.2 -> net -0.5 (net loss)
  ad user value 0.7 -> net +0.0 (neutral)
  ad user value 1.4 -> net +0.7 (net gain)
```

## Notes

- An irrelevant ad (0.2) displacing a 0.7 organic item is a 0.5 loss; a
  relevant ad (1.4) is a 0.7 gain.
- The externality is the difference between the ad's user value and the
  organic value it replaced — why the value tree prices the combination
  rather than banning ads.
