"""Prompt budget, read: the list that does not fit in the prompt.

Stage 31 scores candidates with an LLM prompt. This script reads what
happens when the candidate list exceeds the token budget and the list
must be truncated before the LLM sees it.

Run:
    uv run python core/token_budget.py
"""

from __future__ import annotations


def main() -> None:
    # (doc, LLM score if seen, position in the full list)
    docs = [
        ("d1", 0.95, 1),
        ("d2", 0.90, 2),
        ("d3", 0.85, 3),
        ("d4", 0.80, 4),
        ("d5", 0.99, 5),
    ]
    budget = 4
    seen = [d for d, s, p in docs if p <= budget]
    unseen = [d for d, s, p in docs if p > budget]
    best_unseen = max((s for d, s, p in docs if p > budget), default=0.0)
    print("prompt token budget, read (list of 5, budget 4):")
    print(f"  LLM sees: {seen}")
    print(f"  truncated: {unseen}")
    print(f"  best truncated score: {best_unseen:.2f}")
    print("\nreading: d5 scores 0.99 but sits outside the budget, so the")
    print("LLM never sees it and the pointwise order decides its fate.")
    print("The prompt budget is the LLM ranker's recall boundary — the")
    print("same cutoff question stage 22 asked, with tokens instead of")
    print("milliseconds.")


if __name__ == "__main__":
    main()
