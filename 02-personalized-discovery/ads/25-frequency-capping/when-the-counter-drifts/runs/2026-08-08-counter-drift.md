# Run — the counter-drift audit

**Date:** 2026-08-08
**Command:** `uv run python core/counter_drift.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.13s.
**Cost:** \$0 (local lane).

## Purpose

The stage run reads a decay curve and reads the cap off it. The cap is
only as good as the counter that feeds it, and the counter is an
identity object — a cookie, an app install id, a logged-in user id.
This detour asks what happens when identity fails: the counter resets
to zero and the cap starts over, so the same human is served past the
useful exposure range. It simulates 10,000 users (fixed seed) with the
stage's decay curve, cap 3, 25 percent of users losing their counter
once and 5 percent twice, at random true exposures inside the cap
range.

## Output

```
counter-drift audit: 10,000 users, fixed seed
cap 3; 25% of users lose their counter once, 5% twice

    campaign  impressions  exp. clicks clicks/imp  dead share
     correct        30000       1200.0     0.0400        0.0%
  counter drift        36167       1285.6     0.0355        3.1%

extra impressions served: 6167
extra expected clicks: +85.6 (+7.1%)

reading: the cap reads the counter, not the human. When the
counter resets, the cap restarts and the user is served past
the useful exposure range at one-third of the click value.
The fix is identity reconciliation (device graph, login
bridge) or a cap that treats the missing history as censored
exposure instead of zero.
```

## Notes

- With a correct counter the campaign serves 30,000 impressions at
  0.0400 clicks per impression. With 30 percent of users losing their
  counter at least once, the same campaign serves 36,167 impressions —
  6,167 extra, clicked at about one-third of the first-three rate
  (85.6 extra clicks on 6,167 extra impressions, 0.0139 versus 0.0400)
  — and the dead share (served at or below 0.005 CTR) rises from 0.0 to
  3.1 percent.
- The cap reads the counter, not the human. The fix is identity
  reconciliation (device graph, login bridge) or a cap that treats the
  missing history as censored exposure instead of zero — the same
  survival-style logic the delayed-feedback stage uses for labels.
- Reset times drawn uniformly from the exposures the cap would still
  serve (1..3), fixed seed. Illustrative and deterministic, not real
  identity-graph logs.
