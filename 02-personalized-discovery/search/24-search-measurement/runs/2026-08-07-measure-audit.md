# Run — the funnel audit over the slice log

**Date:** 2026-08-07
**Command:** `uv run python core/zero_results.py --emit-log /tmp/measure-envelope.json` then `uv run python prod/measure_audit.py /tmp/measure-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Compare each funnel slice with the aggregate — the case-finding that
catches the funnel metric hiding a collapsed slice, and that turns "the
numbers look fine" into "one slice is failing".

## Output

```
funnel audit over the four slices:
  aggregate: 27,000 queries, zero 5.9%, conversion 1.67%

  slice          queries  zero    click   conversion
  desktop-head   10,000  2%   45%   2.00%
  desktop-tail    2,000  8%   38%   1.50%
  mobile-head    12,000  4%   40%   1.80%
  mobile-tail     3,000  25%   22%   0.20%

verdict: HIDDEN SLICE -- the aggregate funnel
(1.67% conversion, 5.9% zero) looks
normal while mobile-tail converts at 0.20% with a 25%
zero-result rate. The slice is a fraction of traffic, so
it barely moves the aggregate — report the funnel per
slice, and treat a slice whose rate is a third of the
aggregate as an incident, not a rounding error.
```

## Notes

- The audit cohort is the search funnel over four slices: device
  crossed with query stratum. Mobile-tail is 3,000 of 27,000 queries
  (11% of traffic) and converts at 0.20% — one eighth of the aggregate
  1.67% — with a 25% zero-result rate.
- The slice barely moves the aggregate (removing it would shift
  conversion to about 1.87%), which is exactly why the aggregate
  cannot be the report: a failing slice that is a small traffic
  fraction is invisible in the mean and incident-sized in its own
  row.
- The funnel per slice is the stage's coverage signal; the
  when-the-session-definition-moves detour adds the second
  consistency check — the funnel is only comparable across time if the
  session definition is frozen.
