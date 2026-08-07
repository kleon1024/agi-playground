"""ANN versus exact, read: recall traded for latency at scale.

Stage 20's dense index serves with approximate nearest neighbors. This
script reads the recall-latency trade as the candidate budget shrinks.

Run:
    uv run python core/ann_read.py
"""

from __future__ import annotations


def exact_recall(n: int, scanned: int) -> float:
    # Exact scans everything; approximate scans a fraction, losing
    # candidates near the decision boundary.
    return 1.0 if scanned >= n else max(0.0, 1.0 - (n - scanned) / n)


def main() -> None:
    n = 100_000
    print("ANN vs exact, read (100,000-item index):")
    for scanned in (100, 1_000, 10_000, 100_000):
        print(f"  scan {scanned:>7,}: recall {exact_recall(n, scanned):.3f}")
    print("\nreading: exact retrieval scans the whole index — full recall,")
    print("full latency. ANN scans a fraction and accepts a recall loss at")
    print("the boundary. The index size decides which is even feasible.")


if __name__ == "__main__":
    main()
