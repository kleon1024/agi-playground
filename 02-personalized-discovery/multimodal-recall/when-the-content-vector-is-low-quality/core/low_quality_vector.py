"""Low-quality content vectors, read: reachable but not retrievable.

Stage 33 makes cold items retrievable through content vectors. This
script reads what happens when the content itself is low quality — a
blurry image, an auto-tag text — and the embedding that comes out is
noisy: the item is in the index, but its vector sits far from its
category, so it is technically reachable and effectively not
retrievable.

The read embeds 12 items across four categories: two clean items per
category (small embedding noise) and one low-quality item per category
(large noise, standing in for the blurry image or the auto-tag text).
Each category query retrieves by cosine similarity, and the read counts
recall@3 for clean and low-quality items separately.

Run:
    uv run python core/low_quality_vector.py
"""

from __future__ import annotations

import math
import random

DIM = 16
SEED = 7
CLEAN_NOISE = 0.08
LOW_QUALITY_NOISE = 0.70


def unit(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    return [x / norm for x in vector]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def main() -> None:
    rng = random.Random(SEED)
    categories = ["A", "B", "C", "D"]
    centroids = {
        cat: unit([rng.gauss(0.0, 1.0) for _ in range(DIM)]) for cat in categories
    }
    items: list[tuple[str, str, bool]] = []  # (name, category, low quality)
    for cat in categories:
        for i in range(3):
            low_quality = i == 2
            items.append((f"{cat}{i + 1}", cat, low_quality))

    def embed(cat: str, low_quality: bool) -> list[float]:
        noise = LOW_QUALITY_NOISE if low_quality else CLEAN_NOISE
        vector = [
            centroids[cat][d] + rng.gauss(0.0, noise) for d in range(DIM)
        ]
        return unit(vector)

    vectors = {name: embed(cat, low) for name, cat, low in items}

    print("low-quality content vectors, read (recall@3):")
    clean_recalled = 0
    low_recalled = 0
    for cat in categories:
        query = unit([centroids[cat][d] + rng.gauss(0.0, 0.02) for d in range(DIM)])
        ranked = sorted(
            vectors.items(), key=lambda kv: cosine(kv[1], query), reverse=True
        )
        top3 = [name for name, _ in ranked[:3]]
        for name, _, low in items:
            if name.startswith(cat) and name in top3:
                if low:
                    low_recalled += 1
                else:
                    clean_recalled += 1
        names = ", ".join(f"{n}{'*' if low else ''}" for n, _, low in items if n.startswith(cat))
        print(f"  category {cat}: top-3 {top3}  (items {names}, "
              f"* = low-quality content)")
    clean_total = sum(1 for _, _, low in items if not low)
    low_total = sum(1 for _, _, low in items if low)
    print(f"  recall@3: clean {clean_recalled}/{clean_total}, "
          f"low-quality {low_recalled}/{low_total}")
    print()
    print("reading: has a vector is not has a usable vector. The")
    print("low-quality item is in the index, but its noisy embedding")
    print("sits far from its category and loses the retrieval race to")
    print("other categories' items. Reachability is a quality property,")
    print("not a presence property: gate content quality before")
    print("embedding and re-embed when the source improves.")


if __name__ == "__main__":
    main()
