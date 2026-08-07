# Run — the new user who is the majority

**Date:** 2026-08-07
**Command:** `uv run python core/new_user_majority.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Show the traffic-mix arithmetic behind a personalization launch: the
aggregate lift is an average over sessions, and when most sessions have
no history the model cannot help most of your traffic — the aggregate
hides the concentration.

## Output

```
new-user majority, read (personalization lift by user slice):
  new (no history)     traffic 70%  lift +0.000
  light history        traffic 20%  lift +0.020
  heavy history        traffic 10%  lift +0.150
  aggregate lift: +0.019
  sessions the model can help: 30%

reading: the aggregate lift +0.019 hides that 70% of traffic
has no history and cannot be personalized at all. The model's
benefit is concentrated in the 30% that can use it — and the
product decision is the cold-start policy (what the 70% see),
not the size of the lift on the 10% who benefit most.
```

## Notes

- The aggregate +0.019 is a weighted average over sessions; the 70%
  no-history slice contributes zero and dilutes the heavy slice's
  +0.150 to a flat headline. Dou, Song and Wen, "A Large-scale
  Evaluation and Analysis of Personalized Search Strategies", WWW 2007,
  measure the same shape: personalization gains depend on user and
  query type, with head queries and low-history users gaining little.
- The decision is the cold-start policy for the 70%, not a bigger
  personalization model for the 10%.
