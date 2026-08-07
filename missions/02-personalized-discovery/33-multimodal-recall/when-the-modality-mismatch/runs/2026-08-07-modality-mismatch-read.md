# Run — when the modality mismatches, executed on the cross-modal gap read

**Date:** 2026-08-07
**Command:** `uv run python core/modality_mismatch.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 33 recalls across modalities. This run scores a text-rich item and an image-only item against a text query.

## Output

```
modality mismatch, read (text query):
  item_x (has text vector): text-text 0.82, text-image 0.55
  item_y (image only): text-text 0.00, text-image 0.60

reading: the image-only item competes through the cross-modal
gap — its text-image score (0.60) is below the text-text score
of the item with text (0.82), even when the image is relevant.
Modality mismatch is a recall bias toward text-rich items.
```

## Notes

- The image-only item competes through the cross-modal gap: its text-image score (0.60) sits below the text-text score of the text item (0.82).
- Modality mismatch is a recall bias toward text-rich items.
