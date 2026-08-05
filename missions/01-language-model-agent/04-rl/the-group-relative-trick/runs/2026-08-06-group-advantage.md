# Run — the group-relative advantage, as arithmetic

**Date:** 2026-08-06
**Command:** `uv run python core/group_advantage.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.01s.
**Cost:** \$0 (local lane).

## Purpose

Ground the group-relative-trick chapter's advantage arithmetic in the exact
formulas `core/grpo.py` uses (std unbiased=False, degenerate threshold
1e-6, advantage denominator std+1e-4, clip epsilon 0.2), on three reward
groups: the all-zeros group of mission 01's 200/200 null, a sparse
grid-world-style group, and a healthy spread.

## Output

```
== mission 01 null: every group member scores exactly 0.0 ==
  rewards: [0.0 x8]
  mean=0.0000  std=0.000000
  degenerate: std < 1e-6, advantage is 0/0, group contributes no gradient

== grid-world-style: two wins in eight, sparse verifier reward ==
  rewards: [0,0,1,0,0,1,0,0]
  mean=0.2500  std=0.433013
  advantages: -0.577 x6, +1.732 x2
  members pushed up: 2, pushed down: 6, zero: 0

== healthy spread ==
  rewards: [0.2,0.5,0.8,1.0,0.3,0.6,0.4,0.9]
  mean=0.5875  std=0.271282
  advantages: -1.428, -0.322, +0.783, +1.520, -1.059, +0.046, -0.691, +1.152
  members pushed up: 4, pushed down: 4, zero: 0
```

## Notes

- The sparse group's two winners carry advantages of +1.732 — three times
  the magnitude of the six losers' -0.577 — because group normalization
  concentrates the update on the members that separated themselves.
- With a hypothetical ratio of 1.5 and eps 0.2, the positive side is capped
  at 1.20*A while the negative side uses the full 1.50*A: the clip is a
  one-sided brake that stops one good group from pushing the policy
  arbitrarily hard, exactly the pessimistic bound `grpo_loss` implements.
- No model was trained; this is the arithmetic the real runs (mission 01's
  200/200 null, mission 06's 1/200 degeneracy) execute.
