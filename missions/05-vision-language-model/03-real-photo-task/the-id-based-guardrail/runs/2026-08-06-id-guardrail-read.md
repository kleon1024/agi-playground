# Run — the image-ID guardrail, read from the recorded real-photo build

**Date:** 2026-08-06
**Command:** `uv run python core/id_guardrail_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the dataset build was the stage's recorded run).

## Purpose

Stage 03 rebuilt the task on real photographs, where the leakage guardrail
changes from pixel hash to COCO image-id. This run reads the record and
lays out the split and the guardrail.

## Output

```
  train images  : 300 (599 QA pairs)
  eval images   : 100 (198 QA pairs)
  image-id overlap between train and eval (must be 0): 0
```

## Notes

- Real photographs essentially never collide by pixel hash, so the
  guardrail moves to image-id disjointness.
- The same real image must not appear in both splits, checked by COCO id,
  not by rendering.
