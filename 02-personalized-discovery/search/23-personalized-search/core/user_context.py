"""Personalized search, read: the query with a user attached.

Stage 23 re-ranks search results with user context. This script shows
two users receiving different orders for the same query.

Run:
    uv run python core/user_context.py
    uv run python core/user_context.py --emit-log /tmp/personal-envelope.json

The `--emit-log` flag writes the audit cohort: a 16-query log crossing
history depth (new, heavy) with query stratum (head, tail), each with
the query-only and personalized NDCG. The production path in
`prod/personal_audit.py` stratifies the personalization lift by both
dimensions — the case-finding that shows who actually benefits.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Audit cohort: NDCG with the query-only ranking and with the
# personalized ranking, by history depth and query stratum. Heavy
# history on tail queries carries the lift; head queries and users
# without history see none.
AUDIT_QUERIES = {
    "heavy": {
        "tail": [
            {"query": "trail gaiters", "base": 0.60, "personal": 0.85},
            {"query": "espresso tamper", "base": 0.60, "personal": 0.85},
            {"query": "chalk bag", "base": 0.60, "personal": 0.85},
            {"query": "dash cam", "base": 0.60, "personal": 0.85},
        ],
        "head": [
            {"query": "running shoes", "base": 0.80, "personal": 0.85},
            {"query": "headphones", "base": 0.80, "personal": 0.85},
            {"query": "phone case", "base": 0.80, "personal": 0.85},
            {"query": "coffee maker", "base": 0.80, "personal": 0.85},
        ],
    },
    "new": {
        "tail": [
            {"query": "trail gaiters", "base": 0.60, "personal": 0.58},
            {"query": "espresso tamper", "base": 0.60, "personal": 0.58},
            {"query": "chalk bag", "base": 0.60, "personal": 0.58},
            {"query": "dash cam", "base": 0.60, "personal": 0.58},
        ],
        "head": [
            {"query": "running shoes", "base": 0.80, "personal": 0.80},
            {"query": "headphones", "base": 0.80, "personal": 0.80},
            {"query": "phone case", "base": 0.80, "personal": 0.80},
            {"query": "coffee maker", "base": 0.80, "personal": 0.80},
        ],
    },
}


def render() -> None:
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the audit cohort as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        Path(args.emit_log).write_text(json.dumps({"queries": AUDIT_QUERIES}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
