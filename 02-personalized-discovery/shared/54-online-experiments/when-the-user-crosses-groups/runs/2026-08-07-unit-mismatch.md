# Run — the analysis unit and carryover, measured

**Date:** 2026-08-07
**Command:** `uv run python core/unit_mismatch.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only (the two-sided t p-value is
computed from the regularized incomplete beta via Lentz's continued
fraction; verified against scipy to 1e-12 in the development check).
**Wall-clock:** 0.2s.
**Cost:** \$0 (local lane).

## Purpose

Measure what happens when the analysis unit does not match the
randomization unit (demo A) and when a treatment session pollutes a later
control session for the same user (demo B).

## Output

```
== Demo A -- unit of analysis ==
500 null experiments, 400 users, 5 sessions each, ICC=0.5
per-session analysis rejected 120 (24.0%)
per-user analysis rejected 21 (4.2%)  [declared alpha 5%]
design effect sqrt(1+(m-1)*ICC) = 1.73x

== Demo B -- carryover ==
true per-session effect: +0.5
carryover: a control session right after a treatment session gets +0.3 residue
naive estimate: +0.428  (bias -0.072)
washout estimate: +0.495  (bias -0.005)
```

## Notes

- Demo A repeats a null experiment 500 times: per-session analysis
  rejects 24.0% of null experiments where the declared alpha is 5%. The
  per-user analysis rejects 4.2%. The design effect matches the closed
  form sqrt(1 + (m-1)*ICC) = sqrt(3) = 1.73.
- Demo B: control sessions that follow a treatment session carry a +0.3
  residue; the naive estimate is 0.428 against a true 0.5. Dropping the
  first session after an arm switch (washout) recovers 0.495.
- Synthetic and deterministic (fixed seeds); the numbers demonstrate the
  mechanism. A real experiment measures its own ICC and carryover window.
