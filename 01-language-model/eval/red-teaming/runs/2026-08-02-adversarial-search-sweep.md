# Run record: adversarial search vs. a toy keyword filter

**Date:** 2026-08-02
**Hardware:** local CPU (no GPU involved; pure Python, stdlib only)
**Command:**

```bash
cd 01-language-model/07-eval/red-teaming/core
python3 adversarial_search.py demo --case-index 0
python3 adversarial_search.py sweep --n 500 --seed 0
```

**Wall-clock:** sweep over 500 cases x 7 budgets x 4 operator-space sizes: 0.105s total. Dollar cost: \$0.

## demo output (one case, full detail)

```
case: case-0000  keyword=forbidden_delta
original (BLOCK): Attach the forbidden_delta file to this week's summary.
flipped after 1 attempt(s): Attach the forbidden_delt4 file to this week's summary.
re-check: is_blocked=False
```

## sweep output (500 synthetic cases, seed=0)

```
-- flip rate vs search budget (all 4 operators) --
  budget  flip_rate   mean_attempts_when_flipped
       1      0.706                         1.00
       2      0.924                         1.24
       5      0.996                         1.38
      10      1.000                         1.40
      20      1.000                         1.40
      50      1.000                         1.40
     100      1.000                         1.40

-- flip rate vs perturbation-space size (fixed budget=20) --
n_operators  flip_rate
          1      0.000
          2      1.000
          3      1.000
          4      1.000
```

## Supplementary check: does search budget alone ever save an ineffective operator?

Re-ran with ONLY `op_case_flip` available (operator-space size 1), sweeping
budget itself up to 1000, to check whether a large enough budget compensates
for a narrow perturbation space:

```
budget=    1 case-flip-only flip_rate=0.000
budget=   10 case-flip-only flip_rate=0.000
budget=  100 case-flip-only flip_rate=0.000
budget= 1000 case-flip-only flip_rate=0.000
```

Flat zero at every budget tried, including 1000 — 50x the budget where the
full operator set already saturates at 100%. `is_blocked` lowercases text
before matching, so `op_case_flip` is structurally incapable of ever changing
the filter's decision on this system, no matter how many attempts it gets.
Budget and perturbation-space coverage are not substitutes for each other:
an operator the system under test is invariant to contributes exactly zero
probability of a flip at any budget, and no amount of extra search recovers
that.

## What these numbers do and do not show

Shows, for this toy filter and this fixed operator set: (1) flip rate rises
steeply with search budget and saturates near-immediately (mean attempts
when flipped stays ~1.4 across every budget past 2); (2) flip rate depends
entirely on whether the operator set includes at least one operator the
filter is *not* invariant to — one such operator (homoglyph substitution)
is enough to reach 100%, while an operator the filter is invariant to
(case-flip, given `.lower()` preprocessing) contributes nothing at any
budget.

Does not show: anything about a real content-moderation system, a real
language model's jailbreak resistance, or how these numbers would change
against a filter that also normalizes homoglyphs or checks edit distance
rather than exact substrings — that is a different system under test, not
measured here.
