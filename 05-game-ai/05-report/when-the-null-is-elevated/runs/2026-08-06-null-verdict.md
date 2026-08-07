# Run — the null verdict's structure, read from the full-chain report

**Date:** 2026-08-06
**Command:** `uv run python core/null_verdict.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.01s (tabulates the recorded report).
**Cost:** \$0 (local lane).

## Purpose

Mission 06's full-chain report returned MET as an honest null result. This
run tabulates the two environments' null evidence and reads the verdict
structure — why the acceptance bar's second disjunct makes MET-as-null the
correct reading.

## Output

```
acceptance: beats both baselines beyond spread, OR an honest
null result with mission 01's own rigor

  grid-world: greedy decode loses decisively to both baselines
  MiniGrid:   honest null — 100% degenerate steps, 0% eval success

  verdict: MET (as an honest null result, across two environments)
```

## Notes

- The grid-world arm alone would read NOT MET (decisive losses), and the
  report leaves that verdict standing. The full-chain verdict evaluates the
  acceptance bar's second disjunct: with MiniGrid's 100% degenerate steps
  and 0% eval success reported with the mission's rigor, the null is a real
  result — which is what MET-as-null means.
- The disjunct exists so a rigorous negative is a deliverable, not a
  failure: the mission proved the boundary (when GRPO's cold start is
  total) rather than claiming an outcome it did not reach.
