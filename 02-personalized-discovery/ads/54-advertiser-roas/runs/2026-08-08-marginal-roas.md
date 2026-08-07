# Run — marginal versus average ROAS, does the average hide the margin

**Date:** 2026-08-08
**Command:** `uv run python core/marginal_roas.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 54's executed lifecycle tracks one advertiser's weekly ROAS as
conversions decay. This audit asks the industrial question that average
ROAS skips: the advertiser scales at the margin, and the average return
can clear the target while the marginal dollar is already below it. The
run splits spend into \$500 increments over a concave conversion curve
(fixed \$28 average order value, 5.0 target ROAS) and measures average
and marginal ROAS at every spend level.

## Output

```
marginal versus average ROAS, audited (aov $28, target 5.0):
 spend | conversions | average ROAS | marginal ROAS over last increment
 $ 1000 |        310 |           8.68 |     -
 $ 1500 |        403 |           7.52 |    5.21
 $ 2000 |        473 |           6.62 |    3.92
 $ 2500 |        523 |           5.86 |    2.80
 $ 3000 |        558 |           5.21 |    1.96

reading: average ROAS stays above the target of 5.0 at
every spend level (5.21 at $3,000), while the marginal
dollar falls below it after the first increment (marginal 1.96
on the last $500). The average hides the margin: a budget
decided on average ROAS keeps spending where the next dollar
already loses against the target.
```

## Notes

- The conversion curve is concave and declared: each \$500 increment
  adds fewer conversions (93, 70, 50, 35), so marginal ROAS falls
  monotonically while average ROAS decays more slowly.
- Average ROAS stays above the 5.0 target at every spend level (8.68
  down to 5.21), while marginal ROAS clears 5.0 only on the first
  increment (5.21) and sits at 1.96 on the last \$500.
- A budget decided on average ROAS keeps spending to \$3,000; a budget
  decided on marginal ROAS stops at \$1,500, where the next increment
  falls below the target. The two rules disagree by \$1,500 of spend.
- The audit demonstrates the mechanism; real budget decisions need the
  measured marginal conversion curve and the advertiser's actual
  marginal target, which come from the incrementality experiments
  stage 30 measures.
