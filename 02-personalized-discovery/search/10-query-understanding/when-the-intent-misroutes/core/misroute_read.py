"""The intent that misroutes, read: what the path decision costs.

Stage 10's classifier assigns one intent per query, and that intent
decides which retrieval path runs — entity pages for navigational,
price-bearing results for transactional, guide content for
informational. The failure mode this chapter exists for is the query
whose keywords fire two intents (or none): rule order or the default
fallback picks a path silently, the candidate set is the wrong type,
and no ranker downstream can recover. This script routes each query by
the classifier and by the oracle, and measures NDCG@3 of the routed
list — the cost of the misroute.

Run:
    uv run python core/misroute_read.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
from query_understanding import classify, normalize, tokenize

# (doc, type) — the corpus each retrieval path serves.
DOCS = [
    ("iphone 17 pro specs", "navigational"),
    ("nike air max size 9", "navigational"),
    ("wireless headphones noise cancelling", "navigational"),
    ("redmi note 13 specs", "navigational"),
    ("how to fix iphone screen", "informational"),
    ("how to choose running shoes", "informational"),
    ("how to fix sleep schedule", "informational"),
    ("iphone vs pixel comparison", "informational"),
    ("nike vs adidas comparison", "informational"),
    ("iphone 17 pro price singapore", "transactional"),
    ("cheap running shoes sale", "transactional"),
    ("headphones price comparison", "transactional"),
    ("redmi note 13 price", "transactional"),
]

# (query, oracle intent, per-type relevance grades). The grades say what a
# user would accept: the primary type is 3, an adjacent type the query also
# tolerates is 1, the rest are 0.
QUERIES = [
    (
        "buy nike running shoes",
        "transactional",
        {"transactional": 3, "navigational": 1, "informational": 0},
    ),
    (
        "how to fix sleep schedule",
        "informational",
        {"informational": 3, "navigational": 0, "transactional": 0},
    ),
    (
        "best wireless headphones 2026",
        "navigational",
        {"navigational": 3, "informational": 1, "transactional": 0},
    ),
    (
        "cheap how to fix iphone screen",
        "informational",
        {"informational": 3, "transactional": 1, "navigational": 0},
    ),
    (
        "how to buy iphone",
        "informational",
        {"informational": 3, "transactional": 1, "navigational": 0},
    ),
    (
        "redmi note 13 price vs poco x6",
        "informational",
        {"informational": 3, "transactional": 1, "navigational": 0},
    ),
    (
        "nike or adidas",
        "informational",
        {"informational": 3, "navigational": 1, "transactional": 0},
    ),
]


def path_docs(intent: str) -> list[str]:
    return [doc for doc, kind in DOCS if kind == intent]


def ndcg3(grades: list[int]) -> float:
    dcg = sum(g / (1 if i == 0 else i) for i, g in enumerate(grades[:3], start=1))
    # The ideal is the oracle path: its top three docs at the primary grade.
    # A wrong path carrying only adjacent-grade (1) docs cannot normalize
    # itself to 1.0 by being uniformly weak.
    return dcg / 5.5


def routed_ndcg(intent: str, relevance: dict[str, int]) -> float:
    grades = [relevance[kind] for _, kind in DOCS if kind == intent]
    return ndcg3(grades)


def main() -> None:
    print("intent misroute, read (NDCG@3 of the routed candidate set):")
    misrouted = 0
    for query, oracle, relevance in QUERIES:
        classified = classify(normalize(tokenize(query)))
        route_ndcg = routed_ndcg(classified, relevance)
        wrong = classified != oracle
        misrouted += wrong
        note = f"MISROUTED (oracle {oracle})" if wrong else "correct route"
        print(f"  {query:<33} {classified:<14}-> {route_ndcg:.4f}  {note}")
    print(f"\n  {misrouted} of {len(QUERIES)} queries misrouted; every misroute")
    print("  is a collision (two keywords fired) or a no-signal fallback.")
    print("\nreading: the path decision happens before retrieval. When the")
    print("candidate set is the wrong type, the ranker downstream can only")
    print("re-order what it was handed. The fix is dual-path retrieval that")
    print("carries both candidate types and lets ranking decide, at the")
    print("cost of more candidates per query.")


if __name__ == "__main__":
    main()
