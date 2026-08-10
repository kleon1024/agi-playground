"""Query understanding: tokenize, normalize, and classify a query.

Search begins with the query, and the query is a string with noise:
case, punctuation, stopwords, misspellings, and no explicit intent. This
stage builds the minimal query-understanding pipeline — tokenize,
normalize, classify — and measures what each step does to a small set of
realistic queries. Deterministic, stdlib-only.

Run:
    uv run python core/query_understanding.py
    uv run python core/query_understanding.py --emit-log /tmp/query-understanding-envelope.json

The `--emit-log` flag writes the per-query reads plus the query-log cohort
the production path in `prod/intent_audit.py` stratifies by head and tail,
the way a search team drills into an aggregate intent mix.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

STOPWORDS = {"the", "a", "an", "and", "or", "for", "of", "to", "in", "on"}

QUERIES = [
    "best wireless headphones 2026",
    "buy iPhone 17 Pro Singapore",
    "how to fix sleep schedule",
    "Nike Air Max size 9",
    "cheap flights SIN to NRT",
    "redmi note 13 vs poco x6",
]

# The query log the audit stratifies: (query, frequency class). Head queries
# are the well-formed high-traffic ones; tail queries are short, rare, and
# ambiguous — the long tail a keyword classifier was not tuned on.
LOG = [
    ("best wireless headphones 2026", "head"),
    ("buy iPhone 17 Pro Singapore", "head"),
    ("how to fix sleep schedule", "head"),
    ("Nike Air Max size 9", "head"),
    ("cheap flights SIN to NRT", "head"),
    ("redmi note 13 vs poco x6", "head"),
    ("wireless earbuds noise cancelling", "head"),
    ("buy nike running shoes", "head"),
    ("iphone 17 pro price", "head"),
    ("how to choose running shoes", "head"),
    ("samsung s25 vs iphone 17", "head"),
    ("headphones price comparison 2026", "head"),
    ("buy", "tail"),
    ("cheap", "tail"),
    ("reviews", "tail"),
    ("how", "tail"),
    ("why", "tail"),
    ("price", "tail"),
    ("fix", "tail"),
    ("vs", "tail"),
    ("best", "tail"),
    ("cheap how to fix iphone screen", "tail"),
    ("how to buy iphone", "tail"),
    ("redmi note 13 price vs poco x6", "tail"),
    ("best price wireless headphones", "tail"),
    ("why is iphone expensive", "tail"),
    ("nike or adidas", "tail"),
    ("phone screen fix near me", "tail"),
    ("airpods alternative", "tail"),
    ("how much is iphone 17", "tail"),
    ("cheap watch", "tail"),
    ("watch", "tail"),
]


def tokenize(q: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", q.lower())


def normalize(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in STOPWORDS]


def classify(tokens: list[str]) -> str:
    fired = intent_signals(tokens)
    return fired[0] if fired else "navigational"


def intent_signals(tokens: list[str]) -> list[str]:
    """The intent classes whose keywords fired, in rule order.

    The classifier checks transactional before informational; a query whose
    keywords fire both (\"how to buy iphone\") is silently assigned by rule
    order, which is the collision the audit counts.
    """
    joined = " ".join(tokens)
    fired = []
    if any(w in joined for w in ("buy", "cheap", "price", "deal", "order")):
        fired.append("transactional")
    if any(w in joined for w in ("how", "why", "what is", "fix", "vs")):
        fired.append("informational")
    return fired


def row(query: str, freq: str = "") -> dict[str, object]:
    raw = tokenize(query)
    norm = normalize(raw)
    signals = intent_signals(norm)
    return {
        "query": query,
        "freq": freq,
        "tokens": len(norm),
        "norm": norm,
        "signals": signals,
        "intent": signals[0] if signals else "navigational",
    }


def render() -> None:
    print("query understanding, read per query:")
    for q in QUERIES:
        raw = tokenize(q)
        norm = normalize(raw)
        intent = classify(norm)
        print(f"  '{q}'")
        print(f"    raw {raw} -> normalized {norm} -> {intent}")
    all_tokens = [t for q in QUERIES for t in normalize(tokenize(q))]
    print(f"\n  vocabulary across {len(QUERIES)} queries: {len(set(all_tokens))} terms")
    print(f"  most frequent: {Counter(all_tokens).most_common(5)}")
    print("\nreading: normalization removes the noise that would split the")
    print("index (the/A/The all map to one key), and intent classification")
    print("decides which retrieval path — navigational needs exact, ")
    print("transactional needs price, informational needs coverage.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write reads and the query log as JSON")
    args = parser.parse_args()
    render()
    if args.emit_log:
        envelope = {
            "reads": [row(q) for q in QUERIES],
            "log": [row(q, freq) for q, freq in LOG],
        }
        Path(args.emit_log).write_text(json.dumps(envelope))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
