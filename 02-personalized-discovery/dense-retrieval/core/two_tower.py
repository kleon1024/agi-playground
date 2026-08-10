"""Two-tower retrieval, read: query and doc in the same vector space.

Stage 20 retrieves by embedding similarity. This script stands in for the
two towers with concept vectors and reads the ranking it produces.

Run:
    uv run python core/two_tower.py
    uv run python core/two_tower.py --emit-log /tmp/dense-envelope.json

The `--emit-log` flag writes the audit cohort: a 20-query log — 10 head
and 10 tail — with the recall@5 each query gets against the current doc
embeddings and against a stale snapshot from before the last embedding
run. The production path in `prod/dense_audit.py` stratifies the
fresh-versus-stale gap by head and tail, the offline-consistency check
that shows which queries are safe to serve on stale vectors.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in keys)
    na = sum(v * v for v in a.values()) ** 0.5
    nb = sum(v * v for v in b.values()) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


# Audit cohort: recall@5 per query with the current doc embeddings
# ("fresh") and with the snapshot from before the last embedding run
# ("stale"). Head queries are stable under a stale index; tail queries
# — rare terms with few training examples — lose most of their recall
# when the doc vectors drift.
AUDIT_QUERIES = {
    "head": [
        {"query": "running shoes", "fresh": 1.0, "stale": 1.0},
        {"query": "wireless mouse", "fresh": 1.0, "stale": 1.0},
        {"query": "phone case", "fresh": 1.0, "stale": 0.8},
        {"query": "laptop stand", "fresh": 1.0, "stale": 1.0},
        {"query": "usb cable", "fresh": 1.0, "stale": 1.0},
        {"query": "coffee maker", "fresh": 1.0, "stale": 0.8},
        {"query": "bluetooth speaker", "fresh": 1.0, "stale": 1.0},
        {"query": "desk chair", "fresh": 1.0, "stale": 1.0},
        {"query": "yoga mat", "fresh": 1.0, "stale": 0.8},
        {"query": "backpack", "fresh": 1.0, "stale": 1.0},
    ],
    "tail": [
        {"query": "trail gaiters", "fresh": 1.0, "stale": 0.4},
        {"query": "copper water bottle", "fresh": 1.0, "stale": 0.2},
        {"query": "chalk bag", "fresh": 1.0, "stale": 0.6},
        {"query": "shimano cleats", "fresh": 1.0, "stale": 0.4},
        {"query": "raw denim", "fresh": 1.0, "stale": 0.2},
        {"query": "dash cam", "fresh": 1.0, "stale": 0.6},
        {"query": "espresso tamper", "fresh": 1.0, "stale": 0.4},
        {"query": "spinning rod", "fresh": 1.0, "stale": 0.2},
        {"query": "passport holder", "fresh": 1.0, "stale": 0.6},
        {"query": "beard trimmer", "fresh": 1.0, "stale": 0.4},
    ],
}


def render() -> None:
    query = {"running": 1.0, "shoes": 1.0}
    docs = {
        "running footwear": {"running": 1.0, "footwear": 1.0},
        "sneakers": {"athletic": 1.0, "shoes": 1.0},
        "dress shoes": {"formal": 1.0, "shoes": 1.0},
    }
    print("two-tower retrieval, read (cosine to query [running, shoes]):")
    for name, vec in sorted(docs.items(), key=lambda kv: -cosine(query, kv[1])):
        print(f"  {name}: {cosine(query, vec):.3f}")
    print("\nreading: the embedding ranks by meaning — 'running footwear'")
    print("shares the running concept while 'dress shoes' shares only the")
    print("noun. The vector space is the retrieval index; its quality is")
    print("the training data that placed these concepts.")


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
