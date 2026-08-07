# Run — when the creative is stale, executed on the wear model

**Date:** 2026-08-07
**Command:** `uv run python core/stale_creative.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 26 selects creatives. This run reads what logged CTR hides when a
creative has worn and another is new.

## Output

```
stale creative, read:
  creative_a: logged ctr 0.06
  creative_b: logged ctr 0.04
  creative_c: logged ctr 0.03
  creative_a has run 200,000 times; users have seen it
  creative_c is new; logged ctr is a cold-start estimate

reading: logged CTR mixes the creative's quality with its
wear. A stale winner keeps winning the selection on history
while its true value decays — selection needs recency-aware
estimates, not just averages.
```

## Notes

- creative_a's 0.06 logged CTR reflects 200,000 exposures; creative_c's
  0.03 is a cold-start estimate with no wear.
- Logged CTR mixes quality with wear, so selection needs recency-aware
  estimates, not just averages.
