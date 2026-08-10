# Run — the interval that decides, read from the recorded bootstrap run

**Date:** 2026-08-06
**Command:** `uv run python core/interval_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the bootstrap was the chapter's recorded
2026-08-02 run).

## Purpose

The significance chapter compared two item-set sizes with the same true
effect (+0.06). This run reads the JSON and lays out the two rows.

## Output

```
true effect: 0.06 (per-item pass probability)
  condition  n   score A  score B  gap     95% CI        excludes 0
  n=300     300  0.693    0.560   0.133  (0.060, 0.207)  YES
  n=25      25   0.640    0.440   0.200  (-0.040, 0.440)  NO
```

## Notes

- The n=25 gap is larger (0.200 vs 0.133) and the n=300 interval decides:
  point-estimate size and statistical confidence are different axes.
- The interval is the number that ships — a wider interval that includes
  zero means no claim, regardless of how big the observed gap looks.
