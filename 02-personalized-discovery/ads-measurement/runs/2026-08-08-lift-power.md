# Run — lift power, the 0.4-point increment against binomial noise

**Date:** 2026-08-08
**Command:** `uv run python core/power_analysis.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.1s.
**Cost:** \$0 (local lane).

## Purpose

Stage 30's increment is 0.4 points (0.032 exposed versus 0.028 control).
This run asks the statistical question the stage's arithmetic skipped:
is that increment visible to an experiment at the sample sizes an
advertiser can actually buy? It sweeps sample size per arm and effect
size, both over binomial conversion noise with a fixed seed.

## Output

```
incrementality, measured: is the 0.4-point lift visible?
  true rates: exposed 0.032, control 0.028
  true increment: 0.004 (0.4 points)

sample-size sweep (0.4-point increment, fixed seed):
  n per arm | exposed | control | increment | 95% CI         | p
       2000 | 0.0295  | 0.0225  | +0.0070    | -0.0029 to +0.0169 | 0.164  NO
       8000 | 0.0290  | 0.0290  | +0.0000    | -0.0052 to +0.0052 | 1.000  NO
      20000 | 0.0324  | 0.0289  | +0.0036    | +0.0002 to +0.0069 | 0.040  yes
      50000 | 0.0313  | 0.0278  | +0.0034    | +0.0013 to +0.0055 | 0.001  yes
     200000 | 0.0319  | 0.0276  | +0.0043    | +0.0033 to +0.0054 | 0.000  yes
    1000000 | 0.0319  | 0.0282  | +0.0038    | +0.0033 to +0.0042 | 0.000  yes

effect-size sweep at n = 8,000 per arm (fixed seed):
  increment | 95% CI         | p      | visible
  0.004    | -0.0030 to +0.0072 | 0.416 | NO
  0.010    | +0.0105 to +0.0215 | 0.000 | yes
  0.020    | +0.0113 to +0.0232 | 0.000 | yes
  0.050    | +0.0451 to +0.0589 | 0.000 | yes

verdict: the 0.4-point increment is buried in binomial noise
at the sample sizes a small advertiser can reach. The CI
covers zero at 8,000 users per arm (p > 0.05) and only
excludes zero at production-scale spend. A big increment is
visible at the same 8,000-user scale: the experiment is
sized for the effect, and the ads track's 0.4 points is too
small for the traffic most campaigns actually buy.
```

## Notes

- Sample-size sweep (0.4-point increment, seed 42): at 2,000 and 8,000
  users per arm the 95 percent CI covers zero; at 8,000 the observed
  increment is literally 0.0000 — the noise floor swallows the signal.
  The CI first excludes zero at 20,000 per arm (p = 0.040), the
  production-scale spend a big campaign actually reaches.
- Effect-size sweep at 8,000 per arm: the same sample that cannot see
  0.4 points sees a 1-point increment clearly (p < 0.001). The
  experiment is sized for the effect, not the reverse.
- Verdict: the stage's 0.4-point increment is invisible at small
  advertiser scale; measuring it requires production-scale spend, which
  is why incrementality experiments are expensive and why
  Lewis & Rao (2015, QJE) report that measuring the returns to
  advertising is hard even with large field experiments.
