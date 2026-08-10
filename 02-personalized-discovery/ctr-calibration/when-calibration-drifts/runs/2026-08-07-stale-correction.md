# Run — the stale-correction audit

**Date:** 2026-08-07
**Command:** `uv run python core/stale_correction.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

The correction detour fits one multiplicative factor on its training
window. This read asks the follow-up: what happens when the window moves?
It fits the factor on an old window (click rate 0.30) and evaluates it on
a new window where the click rate has risen to 0.50, then compares the
raw and corrected ECE on each window.

## Output

```
stale-correction read: factor fit on the old window, applied to
the new one. The model still predicts ~0.545; the click rate
rose from 0.30 to 0.50.

      window   ECE raw   ECE corrected
         old    0.2450          0.0000
         new    0.0550          0.3000

correction factor fit on old data: 0.5505
```

## Notes

- On the training window the factor (0.5505) drops ECE from 0.2450 to
  0.0000 — the fix works where it was fit. On the new window the same
  factor over-corrects: ECE rises to 0.3000, worse than the 0.0550 the
  raw estimate carried on that window.
- The stale correction is the failure mode behind "the fix stopped
  working": the factor is a point estimate of a rate that moves. The
  durable fix is to refit on a rolling window and monitor ECE on new
  traffic, so the fit's expiration date is measured, not assumed.
- Hand-built predictions and click vectors with no random draws;
  illustrative and deterministic, not real click logs.
