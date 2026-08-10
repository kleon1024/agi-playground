# Run — cut the marginal dollar first, which dollar returns the least

**Date:** 2026-08-08
**Command:** `uv run python core/cut_the_marginal_dollar.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

The stage audit shows average ROAS clearing the target while marginal
ROAS falls below it. This run asks the decision consequence: when the
budget must be cut, which dollar goes first? It uses the same declared
concave conversion curve and \$500 increments, and measures, for every
increment and for the whole budget, the revenue lost per dollar of
spend cut.

## Output

```
cut the marginal dollar first, audited (aov $28, $500 increments):
 cut | spend cut | conversions lost | revenue lost | return per $ cut
 $1000-1500 |        $500 |            93 |        $ 2604 |             5.21
 $1500-2000 |        $500 |            70 |        $ 1960 |             3.92
 $2000-2500 |        $500 |            50 |        $ 1400 |             2.80
 $2500-3000 |        $500 |            35 |        $  980 |             1.96
 all 3000 |        $3000 |           558 |       $15624 |              5.21

reading: cutting the top increment returns $1.96 per dollar
saved; cutting the first increment returns $5.21, and cutting
the whole budget returns the 5.21 average. The marginal dollar
is the first to go: a $500 cut from the top loses the least
revenue and lifts the average ROAS that remains, because the
dollar that returns the least is the one the budget should
have stopped at first.
```

## Notes

- Every row saves the same \$500, but the revenue lost falls from
  \$2,604 on the first increment to \$980 on the top one: the marginal
  dollar returns 1.96x while the first dollar returns 5.21x.
- Cutting the whole \$3,000 budget loses \$15,624, exactly the 5.21
  average — the average is what a lump-sum cut is priced at, which is
  why the average hides the margin: it mixes dollars that return 5.21
  with dollars that return 1.96.
- A \$500 cut from the top also lifts the remaining average ROAS (from
  5.21 to 5.86), so the advertiser defending a ROAS floor cuts from
  the top: the least revenue lost per dollar saved and a higher
  reported return.
- The run demonstrates the mechanism on a declared curve; real
  cut decisions need the measured marginal conversion curve per
  segment, which is the incrementality measurement stage 30 owns.
