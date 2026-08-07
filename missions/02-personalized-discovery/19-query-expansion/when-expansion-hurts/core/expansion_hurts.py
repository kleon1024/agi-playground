"""When expansion hurts, read: the broadened query retrieves noise.

Stage 19 expands queries with synonyms. This script shows the downside:
an expanded query matches more documents, including irrelevant ones.

Run:
    uv run python core/expansion_hurts.py
"""

from __future__ import annotations


def main() -> None:
    docs = {
        "apple fruit recipes": "fruit",
        "apple iphone review": "phone",
        "apple laptop repair": "laptop",
        "apple pie dessert": "dessert",
    }
    query = "apple"
    expanded = {"apple", "fruit", "phone"}
    base_hits = [d for d, c in docs.items() if query in d]
    expanded_hits = [d for d, c in docs.items() if any(t in d for t in expanded)]
    print("expansion hurts, read:")
    print(f"  base query '{query}': {len(base_hits)} hits — all relevant")
    print(f"  expanded: {len(expanded_hits)} hits — including wrong senses")
    wrong = [d for d in expanded_hits if d not in base_hits]
    print(f"  new hits from expansion: {wrong}")
    print("\nreading: expansion trades precision for recall. The phone and")
    print("laptop docs join the result set because 'apple' means phone in")
    print("one context and fruit in another — the ambiguity is the cost.")


if __name__ == "__main__":
    main()
