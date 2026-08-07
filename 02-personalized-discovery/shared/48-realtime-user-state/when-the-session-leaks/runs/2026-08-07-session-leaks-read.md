# Run — when the session leaks, executed on the feature-window leak read

**Date:** 2026-08-07
**Command:** `uv run python core/session_leaks.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 48's detour: the freshest feature there is is also the easiest to
build wrong. This run scores 300 sessions of ten items with a leaky
session feature (the click itself) against an as-of feature (prior
dwells only), measuring the top-1 hit rate and NDCG@10 of each.

## Output

```
session leaks, read (NDCG@10, 300 sessions of 10 items):
  feature           ndcg@10 top-1 hits
  leaky (clicked)     0.245    300/300
  as-of (prior)       0.101     33/300

reading: the leaky feature is the outcome itself - it places
the clicked item first in all 300 sessions, so the eval
reports a perfect top-1 hit rate. At serve time the click has
not happened yet; the model can only use the as-of feature,
which places the target first in 33 of 300 sessions. The gap
between 300/300 and 33/300 is the leak: an offline eval whose
feature window includes the label window validates a model
that cannot exist online. Check feature-vs-label time ordering
before trusting a session feature's eval - the as-of join
from stage 44 applied to session features.
```

## Notes

- The leaky feature places the clicked item first in all 300 sessions —
  a 300/300 top-1 hit rate — because the feature is the outcome itself.
  The as-of feature, built only from events that ended before the
  target's moment, places the target first in 33 of 300 sessions.
- The production signature of this failure is an offline eval that beats
  the online A/B by a wide margin; the fix is a time-order audit of each
  session feature against the label window, the as-of join from stage 44
  applied to session features.
