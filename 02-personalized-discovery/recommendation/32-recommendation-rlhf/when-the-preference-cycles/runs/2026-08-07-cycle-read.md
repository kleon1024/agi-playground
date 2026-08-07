# Run — when the preference cycles, executed on the scalar-model fit

**Date:** 2026-08-07
**Command:** `uv run python core/cyclic_preference.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 32 trains a ranker from pairwise preferences under a scalar
reward. This run fits an Elo-style scalar model to the three-item cycle
A > B, B > C, C > A and reads where the fitted scores contradict the
observed preferences.

## Output

```
cyclic preference, read (A > B, B > C, C > A):
  fitted scalar ratings: A -0.44, B 0.22, C 0.22
  last-update swing after 1000 iterations: 0.659

  pairwise predictions:
    A vs B: predicted A wins (0.34) -- CONTRADICTS
    B vs C: predicted B wins (0.50) -- CONTRADICTS
    C vs A: predicted C wins (0.66) -- matches

  contradictions: 2 of 3 edges

reading: a scalar model is transitive by construction, and a
cycle has no consistent scalar answer — the ratings keep
rotating -- the last-update swing (0.659) does not
decay toward zero, so no fitted score ever settles -- and at
least one observed edge is always predicted wrong. The
pipeline has to detect the cycle (count cyclic triples among
sampled pairs) and either drop the weakest edge or model the
preference as context-dependent instead of a single score
(Zhang et al. 2025).
```

## Notes

- A scalar model is transitive by construction, so the cycle A > B,
  B > C, C > A has no consistent scalar answer. The Elo-style fit
  keeps rotating: the last-update swing after 1,000 iterations is
  0.659, which does not decay toward zero, and 2 of 3 observed edges
  are predicted wrong.
- The fix is detection first — count cyclic triples among the sampled
  pairs — then either drop the weakest edge or model the preference
  as context-dependent. Zhang et al., "Beyond Bradley-Terry Models",
  ICML 2025, arXiv:2410.02197, is the reference for the scalar
  model's limitation.
