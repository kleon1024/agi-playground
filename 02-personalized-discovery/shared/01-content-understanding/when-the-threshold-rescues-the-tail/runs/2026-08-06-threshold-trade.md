# Run — the threshold trade, read from the recorded sweep

**Date:** 2026-08-06
**Command:** `uv run python core/threshold_trade.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded sweep).
**Cost:** \$0 (local lane; the sweep was the stage's recorded synthetic run).

## Purpose

Stage 01's recorded sweep showed the essential trade of the confidence
threshold: raising it improved retained-label accuracy but collapsed cold
coverage. This run reads the recorded numbers and names what the threshold
is actually trading.

## Output

```
the recorded threshold sweep, read:
  catalogue: 300 items
  at 0.00: union 0.00/0.65, cold 100%, label accuracy 96%
  at 0.65: union 72%, cold 25%, label accuracy 100%

reading: raising the threshold did not improve labels — it
removed the least-certain labels, and those live in the tail the
content queue exists to rescue.
```

## Notes

- The trade is real and asymmetric: cold coverage falls 100% to 25% while
  label accuracy rises only 96% to 100% — the marginal labels removed were
  mostly correct, and they were exactly the tail labels.
- Behavioral coverage is threshold-independent (63% throughout): the content
  queue, not the threshold, is what rescues cold items.
