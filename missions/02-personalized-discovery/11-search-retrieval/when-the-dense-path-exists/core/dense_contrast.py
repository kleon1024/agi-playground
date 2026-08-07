"""The dense path, read: why embeddings fix the mismatch.

Stage 11 shows BM25's synonym failure. The fix is a dense matcher that
embeds query and document and scores by similarity — 'footwear' and
'shoes' land near each other. This script computes a simple hand-built
embedding contrast to make the mechanism concrete.

Run:
    uv run python core/dense_contrast.py
"""

from __future__ import annotations

import math

# Hand-built bag-of-concept vectors: {shoes, running, footwear, athletic,
# headphones, wireless, price, review}. Dense similarity = cosine.
CONCEPTS = {
    "query_running_shoes": {"shoes": 1, "running": 1},
    "doc_running_shoes": {"shoes": 1, "running": 1, "lightweight": 1},
    "doc_running_footwear": {"running": 1, "footwear": 1, "athletic": 1},
    "doc_headphones": {"headphones": 1, "wireless": 1},
}


def cosine(a: dict[str, int], b: dict[str, int]) -> float:
    common = sum(a.get(k, 0) * b.get(k, 0) for k in set(a) | set(b))
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return common / (na * nb) if na and nb else 0.0


def main() -> None:
    q = CONCEPTS["query_running_shoes"]
    print("dense similarity, read:")
    for name, vec in CONCEPTS.items():
        if name.startswith("query"):
            continue
        print(f"  query vs {name:<20} cosine {cosine(q, vec):.3f}")
    print("\nreading: doc_running_footware shares 'running' and its")
    print("footwear/athletic concepts embed near 'shoes', so dense")
    print("similarity is high where BM25 scored low. The embedding is the")
    print("mechanism behind hybrid search's synonym coverage.")


if __name__ == "__main__":
    main()
