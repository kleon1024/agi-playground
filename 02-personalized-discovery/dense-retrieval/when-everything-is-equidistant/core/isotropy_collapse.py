"""The space where everything is equidistant, read: anisotropy.

Stage 20 retrieves by embedding similarity. The failure mode this
chapter reads is the embedding space that degenerates: when training
pulls every vector into the same narrow cone, all cosines converge
toward one value and similarity stops separating meaning — the dense
ranking collapses into whichever vector happens to sit closest to the
cone center, which is a frequency prior, not a relevance signal.

Run:
    uv run python core/isotropy_collapse.py
"""

from __future__ import annotations


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def main() -> None:
    # Healthy space: concepts occupy distinct directions, so cosine
    # separates meaning. d1 is relevant to the query, d4 and d5 are not.
    query = [1.0, 0.0, 0.0, 0.0]
    healthy = {
        "d1 relevant": [1.0, 0.2, 0.0, 0.0],
        "d2 related": [0.8, 0.6, 0.0, 0.0],
        "d3 other": [0.0, 1.0, 0.0, 0.0],
        "d4 opposite": [-1.0, 0.0, 0.0, 0.0],
        "d5 unrelated": [0.0, 0.0, 1.0, 0.0],
    }
    # Degenerate space: every vector carries the same dominant
    # component, so cosine converges toward a single value.
    degenerate = {
        "d1 relevant": [4.0, 0.9, 0.1, 0.0],
        "d2 related": [4.0, 0.8, 0.05, 0.1],
        "d3 other": [4.0, 0.7, 0.2, 0.0],
        "d4 opposite": [4.0, 0.6, 0.0, 0.15],
        "d5 unrelated": [4.0, 0.5, 0.3, 0.0],
    }
    print("isotropy collapse, read (cosine to the query vector):")
    print("  healthy space:")
    for name, vec in sorted(healthy.items(), key=lambda kv: -cosine(query, kv[1])):
        print(f"    {name:<12} {cosine(query, vec):+.3f}")
    print("  degenerate space:")
    for name, vec in sorted(degenerate.items(), key=lambda kv: -cosine(query, kv[1])):
        print(f"    {name:<12} {cosine(query, vec):+.3f}")
    print("\nreading: in the healthy space cosine separates d1 (+0.981) from")
    print("d4 (-1.000) across the full range. In the degenerate space all")
    print("five sit inside +0.975..+0.990, the ranking is decided by tiny")
    print("noise offsets, and the unrelated d5 (+0.990) outranks the")
    print("relevant d1 (+0.975). The embedding has stopped being a")
    print("retrieval index — it is a frequency order with a similarity")
    print("label on top.")


if __name__ == "__main__":
    main()
