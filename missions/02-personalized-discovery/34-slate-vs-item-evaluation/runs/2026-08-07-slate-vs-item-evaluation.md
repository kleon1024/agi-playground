# Run — slate versus item evaluation, executed on the diversity-adjusted slate value

**Date:** 2026-08-07
**Command:** `uv run python core/slate_eval.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 34 asks what the user actually experiences: a slate, not items. This run compares two slates on item-score sum and on a diversity-adjusted slate value.

## Output

```
slate evaluation, read:
  slate_a item-score sum: 2.55, slate value 3.06
  slate_b item-score sum: 2.10, slate value 3.36

reading: slate_a wins on item scores (2.55 vs 2.10) but loses
on slate value (3.06 vs 3.36) once diversity counts. Item-level
metrics rank items; the user experiences the slate, which is
why stage 06's mixing and this frontier evaluation agree.
```

## Notes

- slate_a wins on item scores (2.55 vs 2.10) but loses on slate value (3.06 vs 3.36) once diversity counts.
- Item-level metrics rank items; the user experiences the slate, which is why stage 06's mixing and this frontier evaluation agree.
