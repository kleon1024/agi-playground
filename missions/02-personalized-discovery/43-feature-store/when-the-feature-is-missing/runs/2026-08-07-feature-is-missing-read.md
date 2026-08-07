# Run — when the feature is missing, executed on the default-price read

**Date:** 2026-08-07
**Command:** `uv run python core/feature_missing.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 43's store must serve something for a feature that was never
written. This run reads what a default price of zero does to the rank.

## Output

```
feature missing, read (default price 0 vs true price 39):
  P1001: ctr 0.032, default price $49
  P1002: ctr 0.032, default price $89
  P1003: ctr 0.011, default price $19
  P1004: ctr 0.025, default price $0
  rank with default price 0:  ['P1004', 'P1001', 'P1003', 'P1002']
  rank with true price 39:    ['P1001', 'P1004', 'P1003', 'P1002']

reading: the missing price defaulted to zero, which rewards
the item as if it were free and promotes it to the top.
The default is a policy choice that looks like bookkeeping;
the store must make the default explicit and auditable.
```

## Notes

- The zero default promotes P1004 to first place; the true \$39 price drops it to second.
- The default is a policy choice that looks like bookkeeping; the store must make it explicit and auditable.
