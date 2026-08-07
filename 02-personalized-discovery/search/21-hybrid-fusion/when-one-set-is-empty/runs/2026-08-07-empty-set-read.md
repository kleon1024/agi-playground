# Run — when one set is empty, executed on the degraded-fusion model

**Date:** 2026-08-07
**Command:** `uv run python core/empty_set_fusion.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 21 fuses two matcher sets. This run empties the dense set and
reads how the fusion degrades.

## Output

```
empty set fusion, read:
  two matchers: d2:0.033, d1:0.016, d4:0.016, d3:0.016, d5:0.016
  dense empty:  d1:0.016, d2:0.016, d3:0.016

reading: with both matchers, d2 ranks top on agreement; with
the dense set empty, the fusion is just the lexical ranking. The
hybrid degrades silently into whichever matcher is alive — which
is why fusion needs a health check per set.
```

## Notes

- With both matchers d2 tops the list; with the dense set empty the
  fusion is exactly the lexical ranking.
- The degradation is silent, which is why hybrid fusion needs a health
  check per matcher rather than a single aggregate signal.
