# Run — when fatigue hits, executed on the expected-click model

**Date:** 2026-08-07
**Command:** `uv run python core/fatigue_hits.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 25 caps frequency. This run compares expected clicks between a
capped and an uncapped campaign over one million impressions.

## Output

```
fatigue, read (1,000,000 impressions):
  capped at 3:  40,000 expected clicks
  uncapped:     22,429 expected clicks
  lost to fatigue: 17,571

reading: more impressions do not buy more clicks once fatigue
sets in — the uncapped run wastes the same budget for fewer
clicks. Fatigue is why the cap exists: it concentrates delivery
where the ad still earns its slot.
```

## Notes

- Over one million impressions the capped campaign earns 40,000
  expected clicks; the uncapped one earns only 22,429.
- More impressions do not buy more clicks once fatigue sets in —
  fatigue is why the cap exists, concentrating delivery where the ad
  still earns its slot.
