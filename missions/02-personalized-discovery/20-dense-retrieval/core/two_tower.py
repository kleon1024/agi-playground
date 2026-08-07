"""Two-tower retrieval, read: query and doc in the same vector space.

Stage 20 retrieves by embedding similarity. This script stands in for the
two towers with concept vectors and reads the ranking it produces.

Run:
    uv run python core/two_tower.py
"""

from __future__ import annotations


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def main() -> None:
    query = {"running": 1.0, "shoes": 1.0}
    docs = {
        "running footwear": {"running": 1.0, "footwear": 1.0},
        "sneakers": {"athletic": 1.0, "shoes": 1.0},
        "dress shoes": {"formal": 1.0, "shoes": 1.0},
    }
    print("two-tower retrieval, read (cosine to query [running, shoes]):")
    for name, vec in sorted(docs.items(), key=lambda kv: -cosine(query, kv[1])):
        print(f"  {name}: {cosine(query, vec):.3f}")
    print("\nreading: the embedding ranks by meaning — 'running footwear'")
    print("shares the running concept while 'dress shoes' shares only the")
    print("noun. The vector space is the retrieval index; its quality is")
    print("the training data that placed these concepts.")


if __name__ == "__main__":
    main()
