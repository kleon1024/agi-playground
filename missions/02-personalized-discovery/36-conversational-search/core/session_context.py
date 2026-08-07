"""Conversational search, read: the follow-up that needs the first turn.

Stage 36 is the frontier of search: a multi-turn session where the
second query is only meaningful with the first. This script reads how
session context resolves an ambiguous follow-up.

Run:
    uv run python core/session_context.py
"""

from __future__ import annotations


def main() -> None:
    first = "best running shoes for marathons"
    follow_up = "what about the cheaper ones"
    # Candidate intents for the follow-up, scored with and without context.
    candidates = [
        ("cheaper marathon shoes", 0.8, 0.2),
        ("cheaper headphones", 0.1, 0.6),
        ("cheaper laptops", 0.1, 0.2),
    ]
    print("conversational search, read:")
    print(f"  turn 1: '{first}'")
    print(f"  turn 2: '{follow_up}'")
    print("  candidate intents (with context, without):")
    for name, with_ctx, without in candidates:
        print(f"    {name}: {with_ctx} vs {without}")
    winner = max(candidates, key=lambda x: x[1])
    print(f"  resolved: {winner[0]}")
    print("\nreading: without context the follow-up is ambiguous; with the")
    print("session it resolves to the cheaper marathon shoes. The query")
    print("is only part of the input — the session is the other part.")


if __name__ == "__main__":
    main()
