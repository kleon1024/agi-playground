# Run — the five acceptance lines, read from the recorded outcome report

**Date:** 2026-08-06
**Command:** `uv run python core/lines_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded outcome report).
**Cost:** \$0 (local lane).

## Purpose

Stage 02's MET verdict rests on five acceptance lines independently. This
run reads the recorded report and lays out each line.

## Output

```
  codec MSE 0.0111 vs silence 0.3251 / mean-signal 0.3001
  LM completion MSE 0.2581 vs both baselines
  oracle MSE 0.0113 (sanity check)
  quality gap: ZERO (30/30 identical token sequences, max logit gap 1.19e-05)
  no change was required to reused serving code
  VERDICT: MET
```

## Notes

- MET depends on all five lines independently: codec and LM each beat both
  baselines, the gap is a true zero, latency is measured at two scales,
  and no reused serving code changes.
- Flip any one and the verdict changes — the report states that
  explicitly.
