"""Parse swings, read: the same query parses differently across samples.

Stage 37 parses a raw query with an LLM. This script reads what happens
when sampling produces different parses for the same string: the intent
swings, and a low-confidence judgment call flips the retrieval path.

Run:
    uv run python core/parse_swing.py
"""

from __future__ import annotations

from collections import Counter

CASES = [
    (
        "apple watch",
        ["product_search", "product_search", "service_search", "product_search", "service_search"],
    ),
    (
        "check my balance",
        ["bank_balance", "game_balance", "account_summary", "bank_balance", "game_balance"],
    ),
]


def main() -> None:
    print("parse swing, read (5 samples per query):")
    for query, parses in CASES:
        top, n = Counter(parses).most_common(1)[0]
        print(f"  '{query}'")
        for parse in parses:
            print(f"    {parse}")
        print(f"  majority: {top} ({n}/5)")
    print("\nreading: temperature sampling makes the parse a distribution,")
    print("not a point. 'apple watch' splits 3-2 between product and")
    print("service, and the minority parse routes to a different retrieval")
    print("path. 'check my balance' has no 3/5 majority at all. Sampling")
    print("plus majority (self-consistency) stabilizes the clear cases; a")
    print("thin majority means the query is a judgment call and should")
    print("broaden or clarify, not commit.")


if __name__ == "__main__":
    main()
