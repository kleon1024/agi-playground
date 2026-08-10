"""When top-K is not preserved: the final ranker's best twenty barely
survive a pre-rank cut that was optimized for clicks.

Run:
    uv run python core/topk_not_preserved.py
"""

from __future__ import annotations

import math
import random


def sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-min(max(z, -30.0), 30.0)))


def main() -> None:
    rng = random.Random(83)
    m = 1000
    final = [rng.random() ** 2 for _ in range(m)]  # heavy tail of quality
    clicks = [f * (0.2 + 0.8 * rng.random()) for f in final]
    cut = 80
    top = 20
    top_final = sorted(range(m), key=lambda i: final[i], reverse=True)[:top]
    surv = set(sorted(range(m), key=lambda i: clicks[i], reverse=True)[:cut])
    recall = len(set(top_final) & surv) / top
    print("when top-k is not preserved, read (pre-rank cut by clicks):")
    print(f"  catalogue {m}, pre-rank cut {cut}, final top {top}")
    print(f"  final top-{top} surviving the cut: {int(recall * top)} of {top}")
    print()
    print("reading: clicking is not the same as valuing, and a click-optimized")
    print("pre-rank can eject most of the items the final ranker would have")
    print("chosen before it ever sees them. this is the metric to watch across")
    print("the cascade — top-K recall at the cut — because no downstream model")
    print("can re-rank an item the cut already removed.")


if __name__ == "__main__":
    main()
