"""Modality mismatch, read: the query and the item in different spaces.

Stage 33 retrieves by multimodal embeddings. This script reads the
similarity gap when the query is text and the item's only vector is
image-based.

Run:
    uv run python core/modality_mismatch.py
"""

from __future__ import annotations


def main() -> None:
    # (item, text-text cosine, text-image cosine)
    items = [
        ("item_x (has text vector)", 0.82, 0.55),
        ("item_y (image only)", 0.0, 0.60),
    ]
    print("modality mismatch, read (text query):")
    for name, text_cos, image_cos in items:
        print(f"  {name}: text-text {text_cos:.2f}, text-image {image_cos:.2f}")
    print("\nreading: the image-only item competes through the cross-modal")
    print("gap — its text-image score (0.60) is below the text-text score")
    print("of the item with text (0.82), even when the image is relevant.")
    print("Modality mismatch is a recall bias toward text-rich items.")


if __name__ == "__main__":
    main()
