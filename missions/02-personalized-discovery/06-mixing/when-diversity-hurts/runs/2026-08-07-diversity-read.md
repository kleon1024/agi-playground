# Run — diversity that hurts, executed on the slate constraint

**Date:** 2026-08-07
**Command:** `uv run python core/diversity_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 06 assembles slates with a diversity term. This run prices the
constraint: what relevance the slate gives up to reach a fourth category.

## Output

```
  relevance-only: 3.20 relevance, 3 categories
  forced 4 categories: 2.70 relevance, 4 categories
  cost of the constraint: 0.50 relevance
```

## Notes

- The constraint replaces the second-strongest item (0.90) with the best
  item of a missing category (0.40).
- Diversity is bought with relevance; the mixing stage decides how much
  the user actually wants.
