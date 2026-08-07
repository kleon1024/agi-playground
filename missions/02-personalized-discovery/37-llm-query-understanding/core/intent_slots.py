"""LLM query understanding, read: the query parsed into intent and slots.

Stage 37 is the frontier of query understanding: an LLM parses a raw
query into a structured intent with slots, which is the key space
retrieval must serve. This script reads the parsed structure for three
queries.

Run:
    uv run python core/intent_slots.py
"""

from __future__ import annotations


def main() -> None:
    parsed = [
        ("cheap flights to tokyo", "flight_search", {"origin": None, "dest": "tokyo", "max_price": "cheap"}),
        ("2 bedroom apartment rent", "housing_search", {"bedrooms": 2, "type": "apartment", "action": "rent"}),
        ("how do i return an item", "support", {"topic": "returns"}),
    ]
    print("llm query understanding, read (intent + slots):")
    for query, intent, slots in parsed:
        print(f"  '{query}' -> {intent} {slots}")
    print("\nreading: the raw string becomes a structured key space. A")
    print("missing slot (origin is None) is a decision point: retrieval")
    print("either broadens the query or asks for the slot — the empty-slot")
    print("detour shows the cost of guessing.")


if __name__ == "__main__":
    main()
