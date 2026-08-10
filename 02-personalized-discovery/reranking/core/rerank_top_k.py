"""Reranking, read: the expensive model reorders the top k.

Stage 22 reranks the first stage's top candidates with a richer model.
This script reads the reorder on a small list.

Run:
    uv run python core/rerank_top_k.py
    uv run python core/rerank_top_k.py --emit-log /tmp/rerank-envelope.json

The `--emit-log` flag writes the audit cohort: a 20-query log — 10 head
and 10 tail — with the first-stage and reranked NDCG@10 and NDCG@3 per
query. The production path in `prod/rerank_audit.py` compares the
offline eval k with the served page k, the offline/online consistency
check that catches a reranker approved at @10 while hurting the @3 page.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Audit cohort: NDCG@10 (what the offline eval reports) and NDCG@3 (what
# the page serves) for the first stage and the reranked order. Head
# queries improve on both surfaces; tail queries improve at @10 while
# degrading at @3 — the reranker fixes the middle of the list, which
# the three-slot page never shows.
AUDIT_QUERIES = {
    "head": [
        {"query": "headphones", "first10": 0.70, "rerank10": 0.78, "first3": 0.85, "rerank3": 0.90},
        {"query": "running shoes", "first10": 0.70, "rerank10": 0.78, "first3": 0.85, "rerank3": 0.90},
        {"query": "wireless mouse", "first10": 0.70, "rerank10": 0.78, "first3": 0.85, "rerank3": 0.90},
        {"query": "usb cable", "first10": 0.70, "rerank10": 0.78, "first3": 0.85, "rerank3": 0.90},
        {"query": "phone case", "first10": 0.70, "rerank10": 0.78, "first3": 0.85, "rerank3": 0.90},
        {"query": "laptop stand", "first10": 0.70, "rerank10": 0.78, "first3": 0.85, "rerank3": 0.90},
        {"query": "coffee maker", "first10": 0.70, "rerank10": 0.78, "first3": 0.85, "rerank3": 0.90},
        {"query": "bluetooth speaker", "first10": 0.70, "rerank10": 0.78, "first3": 0.85, "rerank3": 0.90},
        {"query": "desk chair", "first10": 0.70, "rerank10": 0.78, "first3": 0.85, "rerank3": 0.90},
        {"query": "yoga mat", "first10": 0.70, "rerank10": 0.78, "first3": 0.85, "rerank3": 0.90},
    ],
    "tail": [
        {"query": "trail gaiters", "first10": 0.72, "rerank10": 0.80, "first3": 0.90, "rerank3": 0.82},
        {"query": "copper water bottle", "first10": 0.72, "rerank10": 0.80, "first3": 0.90, "rerank3": 0.82},
        {"query": "chalk bag", "first10": 0.72, "rerank10": 0.80, "first3": 0.90, "rerank3": 0.82},
        {"query": "shimano cleats", "first10": 0.72, "rerank10": 0.80, "first3": 0.90, "rerank3": 0.82},
        {"query": "raw denim", "first10": 0.72, "rerank10": 0.80, "first3": 0.90, "rerank3": 0.82},
        {"query": "dash cam", "first10": 0.72, "rerank10": 0.80, "first3": 0.90, "rerank3": 0.82},
        {"query": "espresso tamper", "first10": 0.72, "rerank10": 0.80, "first3": 0.90, "rerank3": 0.82},
        {"query": "spinning rod", "first10": 0.72, "rerank10": 0.80, "first3": 0.90, "rerank3": 0.82},
        {"query": "passport holder", "first10": 0.72, "rerank10": 0.80, "first3": 0.90, "rerank3": 0.82},
        {"query": "beard trimmer", "first10": 0.72, "rerank10": 0.80, "first3": 0.90, "rerank3": 0.82},
    ],
}


def render() -> None:
    # (doc, first-stage score, reranker score)
    docs = [
        ("d1", 0.95, 0.30),
        ("d2", 0.90, 0.85),
        ("d3", 0.85, 0.20),
        ("d4", 0.80, 0.92),
        ("d5", 0.75, 0.45),
    ]
    first = [d for d, _, _ in sorted(docs, key=lambda x: -x[1])]
    reranked = [d for d, _, _ in sorted(docs, key=lambda x: -x[2])]
    print("reranking top k, read:")
    print(f"  first stage:  {first}")
    print(f"  reranker:     {reranked}")
    moved = sum(1 for a, b in zip(first, reranked) if a != b)
    print(f"  positions changed: {moved}/5")
    print("\nreading: the reranker reorders using features the first stage")
    print("cannot afford — d4 jumps from 4th to 1st. The first stage")
    print("recalls, the reranker refines; the division is a latency budget")
    print("split, not a preference.")


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
