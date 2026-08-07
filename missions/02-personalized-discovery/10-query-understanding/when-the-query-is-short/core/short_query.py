"""The short query, read: one word, many intents.

A short query is ambiguous by construction — 'shoes' could be navigational
(the category), transactional (buy shoes), or informational (which are
best). This script runs the stage's classifier over single-word queries
and shows where intent classification needs more signal than the query.

Run:
    uv run python core/short_query.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from query_understanding import normalize, tokenize


def main() -> None:
    queries = ["shoes", "iphone", "flight", "headphones", "fix"]
    print("short queries, read:")
    for q in queries:
        tokens = normalize(tokenize(q))
        print(f"  '{q}' -> {tokens} (single intent, but which?)")
    print("\nreading: a one-word query classifies trivially but carries no")
    print("intent signal — 'shoes' is navigational, transactional, and")
    print("informational at once. The stage's classifier needs the context")
    print("(previous queries, device, time) or must hedge the ranking")
    print("across intents, which is the short-query problem in one line.")


if __name__ == "__main__":
    main()
