"""The sets that disagree entirely, read: fusion with no agreement.

Stage 21 fuses lexical and dense candidate sets. The failure mode this
chapter reads is the query where the two matchers return disjoint
lists: there is no overlap, so reciprocal rank fusion has no agreement
to reward, and the fused order is an interleave of two priors — the
top of the page is decided by which matcher's rank-1 happened to score
higher, not by relevance.

Run:
    uv run python core/disjoint_sets.py
"""

from __future__ import annotations


def rrf(rankings: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, 1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank)
    return scores


def main() -> None:
    lexical = ["d1", "d2", "d3", "d4"]
    dense = ["d5", "d6", "d7", "d8"]
    fused = rrf([lexical, dense])
    print("disjoint sets, read (reciprocal rank fusion):")
    for doc, score in sorted(fused.items(), key=lambda kv: -kv[1]):
        where = "lexical" if doc in lexical else "dense"
        print(f"  {doc}: {score:.4f} ({where})")
    top = [doc for doc, _ in sorted(fused.items(), key=lambda kv: -kv[1])[:2]]
    print(f"  fused top-2: {top}")
    print("\nreading: no document appears in both sets, so fusion has")
    print("nothing to reward — every score is a single matcher's rank")
    print("contribution. The fused top is a tie between the two rank-1s")
    print("(both 1/61) and the page order is a coin flip between the")
    print("lexical prior and the dense prior, not a relevance decision.")


if __name__ == "__main__":
    main()
