"""Fan-out tails, read: the tail amplifies with the fan-out factor.

Stage 49 detour: capacity planning sized one server. A real query fans
out to many shards - recall shards, feature servers - and the query is
as slow as its slowest shard. A 1% slow component becomes an 18% slow
query at fan-out 20 while per-shard latency never changes. Hedging -
send two copies, take the first - cuts the amplified tail at the price
of redundant work.

Run:
    uv run python core/fanout_tails.py
"""

from __future__ import annotations

import random

N_QUERIES = 10_000
SHARD_MIX = [(10.0, 0.94), (150.0, 0.05), (800.0, 0.01)]
BUDGET_MS = 500.0
FANOUTS = [1, 5, 20]


def shard_latency(rng: random.Random) -> float:
    draw = rng.random()
    cumulative = 0.0
    for latency, prob in SHARD_MIX:
        cumulative += prob
        if draw < cumulative:
            return latency
    return SHARD_MIX[-1][0]


def simulate() -> dict[str, object]:
    rng = random.Random(13)
    queries: dict[object, list[float]] = {n: [] for n in FANOUTS}
    queries["hedged-20"] = []
    for _ in range(N_QUERIES):
        shards = [shard_latency(rng) for _ in range(20)]
        for n in FANOUTS:
            queries[n].append(max(shards[:n]))
        # Hedged query: two copies of the fan-out-20 query, first wins.
        copy_b = [shard_latency(rng) for _ in range(20)]
        queries["hedged-20"].append(min(max(shards), max(copy_b)))
    return {"queries": queries, "budget_ms": BUDGET_MS, "n_queries": N_QUERIES}


def summarize(values: list[float]) -> tuple[float, float]:
    ordered = sorted(values)
    p99 = ordered[int(len(ordered) * 0.99)]
    over = sum(1 for v in ordered if v > BUDGET_MS) / len(ordered)
    return p99, over


def main() -> None:
    data = simulate()
    queries = data["queries"]
    print("fan-out tails, read (10k queries; shards 10ms/150ms/800ms; "
          "budget 500ms):")
    print(f"  {'fan-out':>9} {'p99':>6} {'over 500ms':>10}")
    for label in (*FANOUTS, "hedged-20"):
        p99, over = summarize(queries[label])
        print(f"  {label:>9} {p99:>6.0f}ms {over:>10.1%}")
    _, single_over = summarize(queries[1])
    _, twenty_over = summarize(queries[20])
    _, hedged_over = summarize(queries["hedged-20"])
    print("\nreading: the query is as slow as its slowest shard, so the")
    print(f"same 1% slow component becomes a {twenty_over:.0%} slow query")
    print(f"at fan-out 20 (from {single_over:.0%} at fan-out 1) while")
    print("per-shard latency never changes - the tail amplifies with the")
    print("fan-out factor. Hedging - two copies, first to finish wins -")
    print(f"cuts the miss rate to {hedged_over:.1%} at 2x the shard work.")
    print("This is the tail at scale: capacity planning for a fan-out")
    print("system must budget for the max over shards, not the mean.")


if __name__ == "__main__":
    main()
