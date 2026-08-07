# Run — feedback loops, executed on the exposure-concentration model

**Date:** 2026-08-07
**Command:** `uv run python core/popularity_collapse.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 45 introduces the feedback loop. This run plays 300 rounds of
show-top-5-and-update-on-clicks and reads how exposure concentrates.

## Output

```
feedback loop, read (300 rounds, show top 5, update on clicks):
  impressions head 5 (true ctr 0.042-0.050): 99%
  impressions tail 5 (true ctr 0.012-0.020): 0%
  catalogue coverage: 20 of 20 items ever shown
  sustained exposure (>=100 impressions): 5 of 20

reading: items 0-4 gather clicks and their estimates rise;
items 5-19 never gather enough to outrank the head, even
where their true rate beats the prior. Exposure entrenches
the first winners and starves the rest. The model's own
output became its training data, so 'more of what works'
works only until the world changes - and the starved tail
is where the change would first be visible.
```

## Notes

- Exposure entrenches the first winners and starves the rest; the head 5 take 99% of impressions, sustained exposure is 5 of 20.
- The model's own output became its training data, so 'more of what works' works only until the world changes.
