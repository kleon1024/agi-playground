# Run — the overcorrecting pacer audit

**Date:** 2026-08-07
**Command:** `uv run python core/overcorrection.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

The variance detour shows a fixed cap. This read replaces the cap with a
feedback controller that re-paces against cumulative deviation from
plan — cap_next = target + gain x (planned - actual) — over demand that
alternates 20/2 per hour, and compares controller gains by total spend,
dark hours, and the hourly spend pattern.

## Output

```
overcorrection read: cap_next = target + gain x (planned - actual);
demand alternates 20 / 2. target per hour = 8.33

   gain   total  dark hrs   hourly spend
    0.5    95.7         0   12    2   14    2   14    2   14    2   15    2   15    2
    1.0   100.0         1   17    2   15    2   15    2   15    2   15    2   15    0
    3.0   100.0         6   20    0   20    0   13    0   20    0   13    0   13    0
```

## Notes

- At gain 0.5 the controller spends something every hour and buys the
  cheap low-demand hours (dark hours 0, total 95.7). At gain 3.0 the
  correction overshoots: the cap floods to the demand ceiling after any
  deficit and clamps to 0 after any surplus — the campaign is dark six
  hours and flooding six, oscillating around the plan it should track.
- The oscillation is a feedback-control failure, not a pacing failure:
  the controller reacts to cumulative error with too much gain, so the
  correction alternates between over- and under-shooting instead of
  converging. Low gain responds slowly (unspent budget when demand
  shifts permanently); high gain oscillates (dark hours now).
- Hand-built demand pattern, no random draws; illustrative and
  deterministic, not a real pacing controller with bid and win-rate
  dynamics.
