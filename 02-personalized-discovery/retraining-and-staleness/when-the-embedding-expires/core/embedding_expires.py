"""Embedding expires, read: the vector computed at ingestion stops
matching the user who moved on.

Stage 46 detour: item embeddings are computed once, when the item is
ingested. User taste drifts; the stale embedding's nearest neighbours
no longer match what users now search for. Refreshing the embeddings
brings recall back.

Run:
    uv run python core/embedding_expires.py
"""

from __future__ import annotations

# (item, stale score vs the query, refreshed score vs the query)
ITEMS = [
    ("P1001", 0.81, 0.30),
    ("P1002", 0.55, 0.85),
    ("P1003", 0.42, 0.78),
    ("P1004", 0.38, 0.22),
    ("P1005", 0.25, 0.60),
]


def recall_at_3(scores: list[tuple[str, float]]) -> int:
    """Number of the top-3 by score that are in the current-relevant set."""
    ranked = [item_id for item_id, _ in sorted(scores, key=lambda r: r[1], reverse=True)]
    return sum(1 for item_id in ranked[:3] if item_id in {"P1002", "P1003", "P1005"})


def main() -> None:
    stale = [(item_id, score) for item_id, score, _ in ITEMS]
    refreshed = [(item_id, score) for item_id, _, score in ITEMS]
    print("embedding expires, read (similarity to the query):")
    print("  item   stale embedding  refreshed embedding")
    for item_id, stale_score, fresh_score in ITEMS:
        print(f"  {item_id}   {stale_score:.2f}             {fresh_score:.2f}")
    print(f"  recall@3 with stale embeddings:     {recall_at_3(stale)}/3")
    print(f"  recall@3 with refreshed embeddings: {recall_at_3(refreshed)}/3")
    print("\nreading: the stale vectors were computed for the taste of")
    print("the day they were ingested; the refreshed ones match the")
    print("current query. Recall recovers 2/3 to 3/3 - the embedding")
    print("is a dated snapshot, and 'retrain' must reach the index,")
    print("not just the model weights.")


if __name__ == "__main__":
    main()
