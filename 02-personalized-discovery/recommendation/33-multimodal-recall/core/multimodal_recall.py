"""Multimodal recall, read: the cold item with a picture and no clicks.

Stage 33 is the frontier of cold-start: a VLM embeds image and text
into one space, so a brand-new item is retrievable from its content
before it has a single interaction. This script reads retrieval
coverage for cold items.

Run:
    uv run python core/multimodal_recall.py
"""

from __future__ import annotations


def main() -> None:
    # (item, has image vector, has text vector, has interactions)
    items = [
        ("item_a", True, True, True),
        ("item_b", True, False, True),
        ("item_c", True, True, False),
        ("item_d", False, True, False),
        ("item_e", False, False, False),
    ]
    print("multimodal recall, read:")
    for name, image, text, interacted in items:
        vectors = []
        if image:
            vectors.append("image")
        if text:
            vectors.append("text")
        reachable = "yes" if vectors else "no"
        cold = "cold" if not interacted else "warm"
        print(f"  {name}: vectors {vectors or ['none']}, {cold}, reachable {reachable}")
    cold_with_vector = sum(
        1 for _, image, text, interacted in items if not interacted and (image or text)
    )
    cold_total = sum(1 for _, _, _, interacted in items if not interacted)
    print(f"  cold items retrievable: {cold_with_vector}/{cold_total}")
    print("\nreading: a cold item is only retrievable if its content")
    print("produces a vector. The VLM is the cold-start bridge: image and")
    print("text embeddings make the never-clicked item reachable, which")
    print("is the frontier version of stage 01's content understanding.")


if __name__ == "__main__":
    main()
