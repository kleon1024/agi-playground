"""Personalized search, read: the query with a user attached.

Stage 23 re-ranks search results with user context. This script shows
two users receiving different orders for the same query.

Run:
    uv run python core/user_context.py
"""

from __future__ import annotations


def main() -> None:
    query = "running shoes"
    # (doc, relevance, user_a affinity, user_b affinity)
    docs = [
        ("trail runners", 0.9, 1.0, 0.0),
        ("track spikes", 0.7, 0.0, 1.0),
        ("road trainers", 0.8, 0.5, 0.4),
    ]
    print(f"personalized search, read (query '{query}', score = relevance + affinity):")
    for user, col in (("A", 2), ("B", 3)):
        scored = [(d, rel + (a if col == 2 else b)) for d, rel, a, b in docs]
        order = [d for d, s in sorted(scored, key=lambda x: -x[1])]
        print(f"  user {user}: {order}")
    print("\nreading: the same query, two orders — user A gets trail runners")
    print("first, user B gets track spikes. Personalization is context")
    print("added to the query; the risk is that the context overrides the")
    print("query's actual intent.")


if __name__ == "__main__":
    main()
