# Run — the long tail a proxy never surfaces, read from the recorded runs

**Date:** 2026-08-06
**Command:** `uv run python core/longtail_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the surface-rate runs were the stage's recorded).

## Purpose

Stage 03 compared cheap-proxy and popularity-only surface rates. This run
reads the record and lays out why popularity-only's long-tail zero is
structural.

## Output

```
  seed 1: long-tail 9 | proxy 0.200/0.111 | popularity 0.100/0.000
  seed 7: long-tail 5 | proxy 0.600/0.200 | popularity 0.400/0.000
  seed 42: long-tail 5 | proxy 0.600/0.200 | popularity 0.400/0.000
  seed 99: long-tail 7 | proxy 0.300/0.143 | popularity 0.100/0.000
  funnel scale: cheap proxy overall 0.150, long-tail 0.000
```

## Notes

- Popularity-only long-tail surface is 0.000 on every seed: a cold item's
  popularity is noise, so it can never rank above a head item on that
  signal alone.
- The zero is structural (by construction), not a tuning miss.
