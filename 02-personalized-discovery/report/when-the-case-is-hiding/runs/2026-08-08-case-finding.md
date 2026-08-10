# Run — the case-finding workflow finds the cases the aggregate hides

**Date:** 2026-08-08
**Command:** `uv run python core/find_the_case.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** about seven seconds.
**Cost:** \$0 (local lane).

## Purpose

Measure whether the case-finding workflow — slice by cohort, slice by
category size, drill to the bottom rows, verify mechanism counts — can
surface two baked-in defects (the five-interaction eligibility boundary and
tail-category recall starvation) after the aggregate evaluation passes.

## Output

```
== 1. the aggregate: it passes ==
15,000 users, 3,000 items, 10 slots, binary relevance
candidate nDCG@10 0.326 vs popularity 0.082 vs item-item CF 0.112
the candidate beats both baselines. the report would pass.

== 2. slice by interaction count: the boundary shows ==
 bucket   users    cand      CF     pop  gap to 21+
    0-4   3,181   0.086   0.096   0.086      -0.332
      5   1,184   0.301   0.121   0.079      -0.117
   6-10   3,639   0.371   0.112   0.080      -0.047
  11-20   4,003   0.417   0.118   0.082      -0.001
    21+   2,993   0.418   0.119   0.082       0.000

== 3. slice by preferred-category size: the tail shows ==
   pref   users    cand      CF     pop  pool cap
   head   8,927   0.424   0.166   0.124       200
    mid   4,503   0.217   0.035   0.021        60
   tail   1,570   0.083   0.025   0.022        10

== 4. drill into the bottom cases ==
worst 50 users by candidate nDCG@10:
  user  int  pref  lands  pool   cand     cf    pop
     8    2  head  False     0  0.000  0.000  0.000
    12    5   mid  False     0  0.000  0.000  0.000
    17    4  tail  False     0  0.000  0.000  0.000
    22    4   mid  False     0  0.000  0.000  0.000
    26    3   mid  False     0  0.000  0.085  0.000
    31    2  head  False     0  0.000  0.000  0.000
    51    2  head  False     0  0.000  0.000  0.000
    55    8   mid  False     0  0.000  0.000  0.000
    58   16  tail   True    10  0.000  0.073  0.095
    64   32   mid  False     0  0.000  0.000  0.000
worst-50 pref mix: {'head': 15, 'mid': 21, 'tail': 14}; interaction mix: {'0-4': 24, '5': 6, '6-10': 10, '11-20': 5, '21+': 5}
tail users are 10% of the population and 28% of the worst 50 (14 of 50).

== 5. verify the mechanisms, not just the cases ==
interactions     5: personalization lands 65% of the time (n=1,184)
interactions  6-10: personalization lands 82% of the time (n=3,639)
interactions 11-20: personalization lands 95% of the time (n=4,003)
interactions   21+: personalization lands 96% of the time (n=2,993)
head recall pool: 1,800 items, capped at 200 by the recall stage
 mid recall pool:   900 items, capped at  60 by the recall stage
tail recall pool:   300 items, capped at  10 by the recall stage

== 6. the verdict ==
the aggregate passed, and the two slices that trail map to the
two mechanisms: the 5-interaction boundary group (personalization
lands 65% vs 95% at 11+) and tail-pref users (a 10-item pool,
exactly one slate, so the ranker has nothing to reorder). these
are the case files the report attaches, each with a named fix
target: move the eligibility boundary or widen the
rare-category recall pool.
```

## Notes

- The users are synthesized with a seeded stdlib RNG (SEED=7) and the two
  defects are baked in with declared probabilities, so the run is
  deterministic and the mechanism counts in section 5 are verifiable
  against the source. Real case-finding runs on logged production rows and
  must record the exact logging cutoff, cohort definition, and revision
  next to the slices.
- The workflow this run exercises — slice, drill, hypothesize, verify — is
  the manual form of automated slice search; Slice Finder (Chung, Kraska,
  Polyzotis, Whang, "Slice Finder: Automated Data Slicing for Model
  Validation", ICDE 2019) enumerates candidate slices statistically, and
  the What-If Tool (Wexler et al., "The What-If Tool: Interactive Probing
  of Machine Learning Models", IEEE VIS 2019, arXiv:1907.04135) makes the
  drill interactive. Both verify on 2026-08-08.
