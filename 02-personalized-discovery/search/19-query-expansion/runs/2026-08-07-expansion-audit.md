# Run — the expansion-lift audit over the query log

**Date:** 2026-08-07
**Command:** `uv run python core/edit_distance.py --emit-log /tmp/expansion-envelope.json` then `uv run python prod/expansion_audit.py /tmp/expansion-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stratify the per-query recall before and after expansion by head and
tail — the case-finding that shows where the expansion lift actually
lives, and whether an aggregate expansion experiment is describing the
whole system or just its tail repair.

## Output

```
expansion-lift audit over the 24-query log:
  aggregate recall: base 0.675 -> expanded 0.908 (lift +0.233)

  stratum  queries  base    expanded  lift     noise/query
  head     12       1.000  1.000     +0.000     1.00
  tail     12       0.350  0.817     +0.467     0.33

verdict: EXPANSION LIFT CONCENTRATED IN THE TAIL -- aggregate lift +0.233 is entirely tail (+0.467);
head queries recover nothing (0.000) and pay for it in noise
(1.00 irrelevant hits per query). An
aggregate expansion experiment reports the lift as if it
applied everywhere; the stratified view says it is a tail
repair, and head traffic should not be expanded at all.
```

## Notes

- The audit cohort is a 24-query log: 12 head queries the catalog
  already covers (base recall 1.000) and 12 tail queries with
  vocabulary mismatches (base recall 0.350). Head queries recover
  nothing from expansion and take on 1.00 irrelevant hit each; tail
  queries recover +0.467 at 0.33 noise each.
- The aggregate says "expansion lifts recall +0.233" — true but
  misleading: every unit of lift is a tail repair, and head traffic is
  paying precision for nothing. The search-team decision that follows
  is to gate expansion by stratum (or by a query-frequency threshold),
  not to ship it everywhere on the strength of the aggregate.
- Xu and Croft, "Query Expansion Using Local and Global Document
  Analysis", SIGIR 1996, is the classic source for the mechanism;
  this audit is the operational check that the classic result assumed
  — the local (per-query) analysis beats global precisely because the
  benefit is query-dependent, which is what head/tail stratification
  exposes.
