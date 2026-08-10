"""LLM disagreement, read: the listwise verdict vs the pointwise order.

Stage 31 adds an LLM listwise ranker. This script reads where the two
orders disagree and whether the disagreement concentrates in the head
or the tail.

Run:
    uv run python core/llm_disagrees.py
"""

from __future__ import annotations


def main() -> None:
    pointwise = ["d1", "d2", "d3", "d4", "d5", "d6"]
    listwise = ["d2", "d1", "d3", "d4", "d5", "d6"]
    head_moved = sum(1 for a, b in zip(pointwise[:3], listwise[:3]) if a != b)
    tail_moved = sum(1 for a, b in zip(pointwise[3:], listwise[3:]) if a != b)
    print("llm disagreement, read:")
    print(f"  pointwise: {pointwise}")
    print(f"  listwise:  {listwise}")
    print(f"  head positions changed: {head_moved}/3")
    print(f"  tail positions changed: {tail_moved}/3")
    print("\nreading: the disagreement concentrates in the head — the LLM")
    print("reorders the top of the list where the user actually looks.")
    print("When the disagreement is in the tail, the LLM is spending its")
    print("latency on positions nobody reaches.")


if __name__ == "__main__":
    main()
