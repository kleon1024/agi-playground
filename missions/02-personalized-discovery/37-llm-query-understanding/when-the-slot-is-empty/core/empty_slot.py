"""Empty slot, read: the missing field changes retrieval.

Stage 37 parses queries into intent and slots. This script reads what
an empty slot does to the retrieval path.

Run:
    uv run python core/empty_slot.py
"""

from __future__ import annotations


def main() -> None:
    # (query, slots, broadened?)
    cases = [
        ("flights to tokyo", {"origin": None, "dest": "tokyo"}, "broaden to all origins"),
        ("flights from sin to tokyo", {"origin": "sin", "dest": "tokyo"}, "exact match"),
    ]
    print("empty slot, read:")
    for query, slots, path in cases:
        print(f"  '{query}': {slots} -> {path}")
    print("\nreading: with origin missing, retrieval broadens to every")
    print("origin — more coverage, less precision. With the slot filled,")
    print("the index answers exactly. The empty slot is a decision: ask,")
    print("broaden, or guess, and each has a measured cost.")


if __name__ == "__main__":
    main()
