# Run — frequency capping, executed on the exposure-decay model

**Date:** 2026-08-07
**Command:** `uv run python core/frequency_cap.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 25 asks why an ad needs a frequency cap. This run reads CTR by
exposure count and shows what an uncapped campaign keeps showing.

## Output

```
frequency cap, read (CTR by exposure count):
  exposure 1: ctr 0.050
  exposure 2: ctr 0.040
  exposure 3: ctr 0.030
  exposure 4: ctr 0.020
  exposure 5: ctr 0.010
  exposure 6: ctr 0.005
  exposure 7: ctr 0.002

reading: CTR decays from 0.05 to 0.002 across seven exposures.
A cap at 3 keeps the high-value exposures; uncapped, the ad
keeps burning impressions at near-zero click value and annoys
the user. The cap is a value decision, not a rule of thumb.
```

## Notes

- CTR decays from 0.050 to 0.002 across seven exposures, so the
  marginal impression's value collapses after the first few.
- The cap is a value decision: it concentrates delivery where the ad
  still earns its slot, which the when-fatigue-hits detour prices.
