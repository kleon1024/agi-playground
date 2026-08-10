"""The cold tail, read: recall concentrates on the head.

Stage 02's recall index returns candidates. This script asks how much of
the candidate set the popular head occupies and what that does to tail
coverage.

Run:
    uv run python core/tail_read.py
"""

from __future__ import annotations


def main() -> None:
    # 1000 items; popularity follows a power law.
    items = list(range(1000))
    popularity = [1000 / (i + 1) for i in items]
    head = items[:100]
    tail = items[100:]
    head_share = sum(popularity[i] for i in head) / sum(popularity)
    tail_share = sum(popularity[i] for i in tail) / sum(popularity)
    # A recall pass that keeps the 200 most popular items.
    kept = sorted(items, key=lambda i: popularity[i], reverse=True)[:200]
    kept_tail = len([i for i in kept if i in tail])
    print("the cold tail, read (1000 items, power-law popularity):")
    print(f"  top 100 items hold {head_share:.1%} of all demand")
    print(f"  items 101-1000 hold {tail_share:.1%}")
    print(f"  a 200-item recall pass keeps {kept_tail}/900 tail items")
    print("\nreading: popularity concentrates, so a recall index that")
    print("learns from demand serves the head and starves the tail. Tail")
    print("coverage is a deliberate trade, not an accident of the index.")


if __name__ == "__main__":
    main()
