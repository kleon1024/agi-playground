# Run — the experiment validity gate over three fixtures

**Date:** 2026-08-07
**Commands:** `uv run python core/ab_validity.py --fixture broken`;
`uv run python core/ab_validity.py --fixture fixed`;
`uv run python core/ab_validity.py --fixture switchback`;
`uv run python core/ab_validity.py --fixture broken --emit-log /tmp/ab-broken.json && uv run python prod/experiment_validity.py /tmp/ab-broken.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 + scipy 1.18.0 for `prod/`.
**Wall-clock:** under one second per fixture; the emitted log is 59,853 rows.
**Cost:** \$0 (local lane).

## Purpose

The stage's gate decides whether an A/B result is readable: the split must
match the declared ratio, the analysis unit must match the randomization
unit, and switchback logs must not carry serial dependence. Three synthetic
fixtures exercise the three failure conditions.

## Output (core)

```
experiment: p95-latency-budget-cut  (units=20000, rows=59853)
  expected split: control 50.0% / treatment 50.0%
  1. allocation ratio: observed 48.36% / 51.64%  chi2=21.52 p=3.51e-06  -> FAIL (SRM)
  2. analysis unit: naive SE 0.0166, clustered SE 0.0175 (1.06x)  -> PASS
  3. serial dependence: N/A (unit-level experiment)

verdict: INVALID -- sample ratio mismatch (SRM): observed 51.64% treatment vs expected 50.00%, chi2=21.52, p=3.51e-06
```

```
experiment: p95-latency-budget-cut  (units=20000, rows=59853)
  expected split: control 50.0% / treatment 50.0%
  1. allocation ratio: observed 49.92% / 50.08%  chi2=0.04 p=0.832  -> PASS
  2. analysis unit: naive SE 0.0165, clustered SE 0.0175 (1.06x)  -> PASS
  3. serial dependence: N/A (unit-level experiment)

verdict: INTERPRETABLE
```

```
experiment: ads-slide-position  (units=28, rows=840)
  expected split: control 50.0% / treatment 50.0%
  1. allocation ratio: observed 39.29% / 60.71%  chi2=1.29 p=0.257  -> PASS
  2. analysis unit: naive SE 0.1254, clustered SE 0.4005 (3.19x)  -> FAIL (unit mismatch)
  3. serial dependence: block-mean lag-1 rho1=0.31  -> FAIL (autocorrelation)

verdict: INVALID -- analysis unit mismatch: clustered SE 0.4005 is 3.19x the naive SE 0.1254
  also failing: serial dependence: block-mean lag-1 autocorrelation rho1=0.31
```

The production path (`prod/experiment_validity.py`) reads the emitted log
with pandas and scipy and returns the same verdicts: INVALID (SRM) for
broken, INTERPRETABLE for fixed, INVALID (analysis unit mismatch, 3.19x SE
gap) for switchback.

## Notes

- The fixtures are explicitly synthetic and illustrative: they demonstrate
  the gate, not a real experiment. `broken.json` and `fixed.json` share the
  same seed, users, and sessions; only the bucket constant differs, so the
  "same log, corrected bucketing" reading is exact.
- The switchback fixture's allocation check passes on 28 blocks even at a
  39/61 observed split: with few randomization units the SRM check has
  almost no power, which is itself a reason switchback is hard.
- The gate is the thing to run against a real experiment log; the fixtures
  exist to prove the gate's verdict logic, not to establish any mission
  outcome.
