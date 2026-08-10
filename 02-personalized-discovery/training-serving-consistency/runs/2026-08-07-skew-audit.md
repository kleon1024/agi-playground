# Run — the logged-versus-live distribution audit over emitted vectors

**Date:** 2026-08-07
**Commands:** `uv run python core/skew.py --emit-log /tmp/skew-envelope.json`;
`uv run python prod/skew_audit.py /tmp/skew-envelope.json`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib for `core/`, pandas 3.0.5 for `prod/`.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 44's skew is silent: the offline eval uses the logged world, so it
agrees with the model by construction. This run is the case-finding half
of the stage: how a team finds a training-serving skew. The core script
emits the logged and live feature vectors as JSON; the production audit
compares the two distributions per feature, the way TensorFlow Data
Validation compares training and serving environments, and names the
features that diverged.

## Output

```
logged-vs-live distribution audit over the emitted vectors:
  items compared: 3
  feature ctr: mean |live-logged| 0.010, max 0.016 (3 items)
  feature price: mean |live-logged| 4.000, max 7.000 (3 items)
  features whose live distribution differs from logged: 2
    ctr
    price

verdict: DIVERGENT -- the live feature distribution no longer
matches the logged one the model trained on. Features above;
the offline ranking is honest about a world that ended.
```

## Notes

- The audit names the feature, which is what lets the owning team decide
  the fix: price moved because a promo ended, ctr moved because the
  served price changed the click rate. A distribution check that only
  said "skew detected" would force a hunt through the pipeline.
- The comparison is the one TensorFlow Data Validation encodes in its
  skew detector, comparing the training and serving environments per
  feature with a configurable threshold (Baylor et al., "TFX: A
  TensorFlow-Based Production-Scale Machine Learning Platform", KDD
  2017; Breck et al., "Data Validation for Machine Learning", SysML
  2019).
