"""Cold image, read: the never-clicked item with only a picture.

Stage 33 retrieves cold items from content vectors. This script reads
the item that has an image vector but no text and no interactions.

Run:
    uv run python core/cold_image.py
"""

from __future__ import annotations


def main() -> None:
    # (item, image vector, text vector, interactions)
    item = ("item_c", True, False, 0)
    image, text, interactions = item[1], item[2], item[3]
    vectors = []
    if image:
        vectors.append("image")
    if text:
        vectors.append("text")
    print("cold image, read:")
    print(f"  {item[0]}: vectors {vectors}, interactions {interactions}")
    print(f"  retrievable by image query: {image}")
    print(f"  retrievable by text query:  {text}")
    print("\nreading: the image vector makes the item reachable for")
    print("image queries but not text ones. The VLM closes one modality's")
    print("gap and leaves the other — a cold item is only as retrievable")
    print("as its available content, per query type.")


if __name__ == "__main__":
    main()
