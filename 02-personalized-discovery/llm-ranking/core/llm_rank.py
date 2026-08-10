"""LLM listwise ranking, read: the model that reorders the whole list.

Stage 31 is the frontier of ranking: a language model scores or reorders
candidates with instruction context, instead of a trained pointwise
scorer. This script reads how a listwise LLM verdict differs from the
pointwise order.

Run:
    uv run python core/llm_rank.py
    uv run python core/llm_rank.py --emit-log /tmp/rank-order-envelope.json

The `--emit-log` flag writes the audit cohort: 20 queries — 10 head and
10 tail — each with the ranking the LLM emits under a forward prompt and
under a reversed prompt. The production path in `prod/rank_order_audit.py`
measures how much the ranking changes with prompt order, the case-finding
that shows which reorders the LLM actually decides.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

# Audit cohort: the ranking the LLM emits under a forward prompt and a
# reversed prompt. Head queries have a clear preference, so the reorder
# is stable; tail queries are judgment calls, so the same candidates
# rank differently depending on how they are written into the prompt.
AUDIT_QUERIES = {
    "head": [
        {"query": "marathon running shoes", "forward": ["d4", "d2", "d5", "d1", "d3"], "reverse": ["d4", "d2", "d5", "d1", "d3"]},
        {"query": "wireless noise cancelling headphones", "forward": ["h2", "h1", "h4", "h3", "h5"], "reverse": ["h2", "h1", "h4", "h3", "h5"]},
        {"query": "budget laptop under 800", "forward": ["l1", "l3", "l2", "l5", "l4"], "reverse": ["l1", "l3", "l2", "l5", "l4"]},
        {"query": "4k monitor for coding", "forward": ["m3", "m1", "m2", "m4", "m5"], "reverse": ["m3", "m1", "m2", "m4", "m5"]},
        {"query": "running socks cushioning", "forward": ["s2", "s1", "s3", "s5", "s4"], "reverse": ["s2", "s1", "s3", "s5", "s4"]},
        {"query": "mechanical keyboard", "forward": ["k1", "k4", "k2", "k3", "k5"], "reverse": ["k1", "k4", "k2", "k3", "k5"]},
        {"query": "trail running vest", "forward": ["v3", "v1", "v2", "v4", "v5"], "reverse": ["v3", "v1", "v2", "v4", "v5"]},
        {"query": "portable espresso maker", "forward": ["e1", "e3", "e2", "e4", "e5"], "reverse": ["e1", "e3", "e2", "e4", "e5"]},
        {"query": "ergonomic desk chair", "forward": ["c2", "c4", "c1", "c3", "c5"], "reverse": ["c2", "c4", "c1", "c3", "c5"]},
        {"query": "yoga mat non slip", "forward": ["y3", "y1", "y2", "y4", "y5"], "reverse": ["y3", "y1", "y2", "y4", "y5"]},
    ],
    "tail": [
        {"query": "wireless earbuds vs earbuds wireless", "forward": ["e2", "e1", "e3", "e4", "e5"], "reverse": ["e1", "e3", "e2", "e5", "e4"]},
        {"query": "lightweight or durable jacket", "forward": ["j3", "j1", "j4", "j2", "j5"], "reverse": ["j1", "j4", "j3", "j5", "j2"]},
        {"query": "smartwatch for fitness", "forward": ["w2", "w4", "w1", "w3", "w5"], "reverse": ["w2", "w1", "w3", "w4", "w5"]},
        {"query": "camera for vlogging", "forward": ["g3", "g2", "g1", "g4", "g5"], "reverse": ["g1", "g3", "g2", "g5", "g4"]},
        {"query": "gaming chair vs office chair", "forward": ["o4", "o1", "o2", "o3", "o5"], "reverse": ["o2", "o4", "o1", "o5", "o3"]},
        {"query": "noise cancelling or open back", "forward": ["n1", "n3", "n2", "n4", "n5"], "reverse": ["n1", "n2", "n4", "n3", "n5"]},
        {"query": "tablet for drawing", "forward": ["t2", "t1", "t4", "t3", "t5"], "reverse": ["t4", "t2", "t1", "t5", "t3"]},
        {"query": "coffee grinder burr", "forward": ["b1", "b3", "b2", "b4", "b5"], "reverse": ["b3", "b1", "b4", "b2", "b5"]},
        {"query": "standing desk height", "forward": ["d3", "d1", "d2", "d5", "d4"], "reverse": ["d1", "d3", "d5", "d2", "d4"]},
        {"query": "backpack for travel", "forward": ["p2", "p4", "p1", "p3", "p5"], "reverse": ["p4", "p1", "p2", "p5", "p3"]},
    ],
}


def render() -> None:
    # (doc, pointwise score, listwise LLM score)
    docs = [
        ("d1", 0.95, 0.55),
        ("d2", 0.90, 0.90),
        ("d3", 0.85, 0.40),
        ("d4", 0.80, 0.95),
        ("d5", 0.75, 0.60),
    ]
    pointwise = [d for d, s, _ in sorted(docs, key=lambda x: -x[1])]
    listwise = [d for d, _, s in sorted(docs, key=lambda x: -x[2])]
    print("llm listwise ranking, read:")
    print(f"  pointwise: {pointwise}")
    print(f"  listwise:  {listwise}")
    moved = sum(1 for a, b in zip(pointwise, listwise) if a != b)
    print(f"  positions changed: {moved}/5")
    print("\nreading: the LLM sees the list as context and reorders it —")
    print("d4 jumps to the top because the instruction reading favors it.")
    print("The frontier cost is latency and prompt length, which is why")
    print("LLM ranking sits at the top of a cascade, not over the whole")
    print("candidate set.")


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
