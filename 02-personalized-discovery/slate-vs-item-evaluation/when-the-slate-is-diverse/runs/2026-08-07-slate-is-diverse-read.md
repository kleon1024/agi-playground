# Run — when the slate is diverse, executed on the coverage-versus-score read

**Date:** 2026-08-07
**Command:** `uv run python core/diverse_slate.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 34 evaluates slates. This run compares the item-score top-3 with a diversity-aware selection.

## Output

```
diverse slate, read:
  item-score top-3: ['i1', 'i2', 'i3']
  diversity-aware:  ['i1', 'i2', 'i4']

reading: the item-score slate is three category-A items; the
diversity-aware slate drops one for coverage. Both are 'best'
under different objectives — the evaluation metric has to say
which one the product wants before the ranker is tuned.
```

## Notes

- The item-score slate is three category-A items; the diversity-aware slate drops one for coverage.
- Both are 'best' under different objectives — the evaluation metric has to say which one the product wants before the ranker is tuned.
