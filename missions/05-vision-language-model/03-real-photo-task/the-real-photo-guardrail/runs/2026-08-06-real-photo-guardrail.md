# Run — the real-photo guardrail, read from the recorded dataset build

**Date:** 2026-08-06
**Command:** `uv run python core/real_photo_guardrail.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.01s (tabulates the recorded dataset record).
**Cost:** \$0 (local lane; no images downloaded).

## Purpose

Stage 03 filtered VQA v2 to scoreable questions and split with an
ID-based disjointness guardrail. This run lays out the two decisions that
differ from the synthetic stage: the filter and the guardrail's key.

## Output

```
real-photo dataset (VQA v2 / COCO, recorded 2026-08-01)
  filter: answer_type kept iff the majority answer is exactly
  scoreable (yes/no or a single alphanumeric word)
  images with >=1 scoreable QA pair: 40,474 of 40,474

  split by answer type (recorded):
split    yes_no   number    other
train       237      101      261
eval         80       25       93

  disjointness guardrail: checked by COCO image id, not pixel
  hash — 0 overlap asserted.
```

## Notes

- The filter matches the synthetic stage's exact-match convention: only
  majority-answerable yes/no or single-word answers are scoreable, which is
  what makes the held-out comparison an exact string match.
- The guardrail keys on COCO image ID, not pixel hash — real photographs
  do not collide procedurally (the synthetic stage's failure mode); they
  overlap by identity, so the guardrail checks the right object and asserts
  0 overlap (plus a post-hoc check on the written records).
