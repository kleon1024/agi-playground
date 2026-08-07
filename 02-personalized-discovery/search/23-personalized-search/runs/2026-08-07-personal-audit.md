# Run — the personalization-lift audit over the query log

**Date:** 2026-08-07
**Command:** `uv run python core/user_context.py --emit-log /tmp/personal-envelope.json` then `uv run python prod/personal_audit.py /tmp/personal-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stratify the personalization lift by history depth and query stratum —
the case-finding that shows who actually benefits from the model being
shipped, and whether an aggregate experiment is describing the whole
traffic or one slice.

## Output

```
personalization-lift audit over the 16-query log:
  aggregate NDCG: base 0.700 -> personal 0.770 (lift +0.070)

  depth  stratum  queries  base    personal  lift
  heavy  tail     4        0.600  0.850   +0.250
  heavy  head     4        0.800  0.850   +0.050
  new    tail     4        0.600  0.580   -0.020
  new    head     4        0.800  0.800   +0.000

verdict: PERSONALIZATION LIFT CONCENTRATED IN HEAVY-HISTORY
USERS -- the aggregate lift +0.070 is entirely the
heavy-history slice (+0.150); new users get
-0.010. The model being shipped only helps users
with history, and only on tail queries. If new users are
most of your traffic, the aggregate hides that most of
your sessions see no benefit — report the lift per slice
and pair the model with a cold-start policy.
```

## Notes

- The audit cohort crosses history depth (heavy, new) with query
  stratum (head, tail), four queries per cell. The lift is +0.250 on
  heavy-history tail queries, +0.050 on heavy head, +0.000 on new head,
  and -0.020 on new tail — where the personalization attempt with no
  history adds noise.
- The aggregate +0.070 is real and misleading: every unit is the
  history-bearing slice. Dou, Song and Wen, "A Large-scale Evaluation
  and Analysis of Personalized Search Strategies", WWW 2007, measure
  the same dependence on user and query type.
- The decision that follows: report the lift per slice, pair the model
  with a cold-start policy for the no-history majority, and check the
  traffic share of each slice before shipping (the
  when-the-new-user-is-the-majority detour prices that mix).
