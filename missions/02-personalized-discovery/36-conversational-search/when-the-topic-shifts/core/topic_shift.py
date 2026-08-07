"""Topic shift, read: the context that no longer applies.

Stage 36 resolves follow-ups with session context. This script reads
the failure when the user changes topic and stale context hijacks the
new query.

Run:
    uv run python core/topic_shift.py
"""

from __future__ import annotations


def main() -> None:
    turns = [
        ("running shoes", "search_marathon"),
        ("what about the cheaper ones", "search_marathon"),
        ("actually, book a hotel in tokyo", "search_hotel"),
        ("any good ones near shibuya", "search_marathon"),  # stale context
    ]
    print("topic shift, read:")
    for query, resolved in turns:
        stale = " (stale)" if resolved == "search_marathon" and "hotel" in query.lower() or "shibuya" in query.lower() and resolved == "search_marathon" else ""
        print(f"  '{query}' -> {resolved}{stale}")
    print("\nreading: the fourth query is about hotels, but the session")
    print("context still points at marathon shoes, so 'near shibuya' is")
    print("misread. Conversation needs a topic boundary: when the intent")
    print("class changes, the old context has to expire.")


if __name__ == "__main__":
    main()
