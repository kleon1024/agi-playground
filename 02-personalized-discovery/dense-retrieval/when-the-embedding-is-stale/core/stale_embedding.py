"""The stale embedding, read: new items are invisible to retrieval.

Stage 20 retrieves by precomputed embeddings. This script shows the cold
start: items added after the last embedding run have no vector and are
unreachable.

Run:
    uv run python core/stale_embedding.py
"""

from __future__ import annotations


def main() -> None:
    embedded = {"item_a": True, "item_b": True, "item_c": True}
    new_items = ["item_d", "item_e"]
    print("stale embeddings, read:")
    for item in new_items:
        print(f"  {item}: embedded? {embedded.get(item, False)} -> unreachable")
    print(f"  catalog: {len(embedded) + len(new_items)} items, "
          f"{len(embedded)} with vectors")
    print("\nreading: retrieval can only return what has a vector. New items")
    print("wait for the next embedding run, and their wait is a recall loss")
    print("for every query they would have answered. Embedding freshness is")
    print("an indexing pipeline decision, not a model detail.")


if __name__ == "__main__":
    main()
