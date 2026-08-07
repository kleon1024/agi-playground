"""One set empty, read: fusion degrades to a single matcher.

Stage 21 fuses two candidate sets. This script reads what happens when
one set is empty — a cold vocabulary or a missing embedding index.

Run:
    uv run python core/empty_set_fusion.py
"""

from __future__ import annotations


def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, 1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank)
    return scores


def main() -> None:
    both = rrf([["d1", "d2", "d3"], ["d2", "d4", "d5"]])
    one = rrf([["d1", "d2", "d3"], []])
    print("empty set fusion, read:")
    print("  two matchers: " + ", ".join(
        f"{d}:{s:.3f}" for d, s in sorted(both.items(), key=lambda kv: -kv[1])))
    print("  dense empty:  " + ", ".join(
        f"{d}:{s:.3f}" for d, s in sorted(one.items(), key=lambda kv: -kv[1])))
    print("\nreading: with both matchers, d2 ranks top on agreement; with")
    print("the dense set empty, the fusion is just the lexical ranking. The")
    print("hybrid degrades silently into whichever matcher is alive — which")
    print("is why fusion needs a health check per set.")


if __name__ == "__main__":
    main()
