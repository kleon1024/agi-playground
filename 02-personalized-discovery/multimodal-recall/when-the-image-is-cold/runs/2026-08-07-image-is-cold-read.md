# Run — when the image is cold, executed on the per-modality reachability read

**Date:** 2026-08-07
**Command:** `uv run python core/cold_image.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 33's VLM creates vectors from content. This run reads whether an image-only cold item is retrievable by each query type.

## Output

```
cold image, read:
  item_c: vectors ['image'], interactions 0
  retrievable by image query: True
  retrievable by text query:  False

reading: the image vector makes the item reachable for
image queries but not text ones. The VLM closes one modality's
gap and leaves the other — a cold item is only as retrievable
as its available content, per query type.
```

## Notes

- The image vector makes the item reachable for image queries but not text ones.
- A cold item is only as retrievable as its available content, per query type.
