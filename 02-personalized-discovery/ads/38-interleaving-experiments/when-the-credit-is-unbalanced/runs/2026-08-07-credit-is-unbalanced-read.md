# Run — when the credit is unbalanced, executed on the shared-document tie read

**Date:** 2026-08-07
**Command:** `uv run python core/credit_tie.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 38 credits clicks to teams. This run reads the click on a document both teams proposed.

## Output

```
credit tie, read:
  team_a: ['d1', 'd2', 'd3']
  team_b: ['d2', 'd4', 'd5']
  clicked: d2 (in team_a True, in team_b True)

reading: d2 appears in both rankings, so the click's credit
is ambiguous — both teams proposed it. Interleaving credit
needs a tie rule (first proposal, random split), or the shared
documents silently blur the comparison.
```

## Notes

- d2 appears in both rankings, so the click's credit is ambiguous — both teams proposed it.
- Interleaving credit needs a tie rule (first proposal, random split), or the shared documents silently blur the comparison.
