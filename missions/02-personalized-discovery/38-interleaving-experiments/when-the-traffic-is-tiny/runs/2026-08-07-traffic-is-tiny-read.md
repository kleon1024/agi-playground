# Run — when the traffic is tiny, executed on the feasibility read

**Date:** 2026-08-07
**Command:** `uv run python core/tiny_traffic.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 38 compares experiment designs. This run checks whether 800 users can support a between-user A/B or interleaving.

## Output

```
tiny traffic, read (800 users available):
  between-user A/B: needs 10,000, available 800, feasible False
  interleaving: needs 400, available 800, feasible True

reading: with 800 users the A/B never reaches significance,
while interleaving needs 400 and ships. For a ranking change
the unit of comparison is the list, not the user — which is
why interleaving is the standard online tool for ranking teams
with limited traffic.
```

## Notes

- With 800 users the A/B never reaches significance (needs 10,000), while interleaving needs 400 and ships.
- For a ranking change the unit of comparison is the list, not the user.
