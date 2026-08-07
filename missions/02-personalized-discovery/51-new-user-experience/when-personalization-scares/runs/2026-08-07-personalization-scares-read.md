# Run — when personalization scares, executed on the page-mix read

**Date:** 2026-08-07
**Command:** `uv run python core/personalization_scares.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 51's detour: a confident onboarding prior ranks the chosen category
above everything. This run reads the category mix of the first page under
three prior strengths.

## Output

```
personalization scares, read (category mix of the first page):
  no prior    strength 0.000: 3 categories, prior category 20% of page
  weak prior  strength 0.006: 3 categories, prior category 30% of page
  strong prior strength 0.020: 3 categories, prior category 40% of page

reading: the onboarding boost concentrates the page on the
category the user clicked once at signup - from a fifth of
the page with no prior to two-fifths with a strong one.
The more the boost owns, the less of the catalogue the user
sees before proving they want it. A page that narrows on a
single signup click reads as a misread, and the user never
comes back to correct it.
```

## Notes

- The chosen category's share of the first page climbs from 20% (no prior) to 40% (strong prior).
- A page that narrows on a single signup click reads as a misread, and the user never comes back to correct it.
