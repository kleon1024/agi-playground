# Run — when the slice hides, executed on the small-slice detection read

**Date:** 2026-08-07
**Command:** `uv run python core/slice_hides.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 47's detour: the slice panel finds a collapse the aggregate cannot
see, and immediately runs into the second failure — the small segment's
daily signal is noise. This run measures detection latency and
false-alarm load for daily and 14-day pooled tests on three segment
sizes, with a real 50% CTR drop at day 10.

## Output

```
slice hides, read (true ctr drops 0.040 -> 0.020 at day 10):
  segment    daily sd  daily detect  daily false  pooled 14d  pooled false
  50k/day    0.00088        day 10            0      day 23             0
  5k/day     0.00277        day 10            0      day 23             0
  500/day    0.00876        day 13            2      day 23             0

reading: the 500/day slice is where the drop lives and where
the signal is noisiest - a daily test fires on pre-drop noise or
waits for a lucky low day, while the pooled window detects
reliably only after 14 days of post-drop evidence. On a small
slice you cannot have both low false alarms and fast detection;
the fix is pooling or shrinkage, not a tighter threshold.
```

## Notes

- The 50k and 5k slices detect the drop on day 10 with zero false
  alarms; the 500/day slice fires twice on pre-drop noise and detects
  the real drop three days late, because its daily standard deviation
  (0.00876) is nearly half the drop itself (0.020).
- The 14-day pooled window detects reliably (day 23, the first day a
  fully post-drop window exists) for every segment, at the price of
  latency — the trade the detour's reading names.
