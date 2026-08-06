# Run — the exact-vs-approximate price, read from the recorded FAISS run

**Date:** 2026-08-06
**Command:** `uv run python core/approx_price.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the FAISS comparison was the stage's recorded run).

## Purpose

Stage 02's prod lane compared exact and approximate ANN at two settings.
This run reads the record and lays out the recall-vs-latency trade.

## Output

```
  default: recall 0.913 at 0.576ms
  ef=64:   recall 0.984 at 0.714ms
  exact:   1.133ms -> 0.911ms
```

## Notes

- Raising ef-search bought recall (0.913 -> 0.984) at a measured latency
  cost (0.576 -> 0.714ms), narrowing but not closing the gap to exact.
- The trade is real and measured, not theoretical: approximate search is a
  recall-for-latency bargain, and the settings are the dial.
