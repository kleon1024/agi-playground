"""LLM listwise ranking, read: the model that reorders the whole list.

Stage 31 is the frontier of ranking: a language model scores or reorders
candidates with instruction context, instead of a trained pointwise
scorer. This script reads how a listwise LLM verdict differs from the
pointwise order.

Run:
    uv run python core/llm_rank.py
"""

from __future__ import annotations


def main() -> None:
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


if __name__ == "__main__":
    main()
