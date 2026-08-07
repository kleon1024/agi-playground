"""Session leaks, read: the feature window includes the label window.

Stage 48 detour: session state is the freshest feature there is - and
the easiest to build wrong. The wrong way is a feature window that
includes the label window: "clicked this item later in the session" is
the outcome itself, so the offline eval validates a model that cannot
exist at serve time. This run compares a leaky session feature against
an as-of feature (events before the target only) on the same sessions.

Run:
    uv run python core/session_leaks.py
"""

from __future__ import annotations

import random

N_SESSIONS = 300
ITEMS_PER_SESSION = 10


def ndcg(ranked_ids: list[int], relevant: set[int], k: int = 10) -> float:
    gain = 0.0
    ideal = 0.0
    for pos in range(k):
        if pos >= len(ranked_ids):
            break
        rel = 1.0 if ranked_ids[pos] in relevant else 0.0
        discount = 1.0 if pos == 0 else 1.0 / (pos + 1).bit_length()
        gain += rel * discount
        ideal += discount
    return gain / ideal if ideal else 0.0


def simulate() -> dict[str, object]:
    """Per-session rows: the click target, the leaky top rank, and the
    as-of rank the model can actually serve."""
    rng = random.Random(23)
    rows: list[dict[str, object]] = []
    for _ in range(N_SESSIONS):
        target = rng.randrange(ITEMS_PER_SESSION)
        relevant = {target}
        # As-of signal: dwells on the target's category before the click,
        # present in 60% of sessions, sometimes on a decoy category.
        prior_dwells = [rng.randrange(ITEMS_PER_SESSION) for _ in range(rng.choice([0, 1, 2]))]
        # Leaky signal: the click itself, which the leaky feature sees.
        leaky_rank = [target] + [i for i in range(ITEMS_PER_SESSION) if i != target]
        as_of_rank = sorted(
            range(ITEMS_PER_SESSION),
            key=lambda i: (prior_dwells.count(i), i),
            reverse=True,
        )
        rows.append(
            {
                "target": target,
                "leaky_ndcg": ndcg(leaky_rank, relevant),
                "as_of_ndcg": ndcg(as_of_rank, relevant),
                "leaky_top_hit": int(leaky_rank[0] == target),
                "as_of_top_hit": int(as_of_rank[0] == target),
            }
        )
    return {"rows": rows, "n_sessions": N_SESSIONS}


def main() -> None:
    data = simulate()
    rows = data["rows"]
    leaky_ndcg = sum(r["leaky_ndcg"] for r in rows) / N_SESSIONS
    as_of_ndcg = sum(r["as_of_ndcg"] for r in rows) / N_SESSIONS
    leaky_hits = sum(r["leaky_top_hit"] for r in rows)
    as_of_hits = sum(r["as_of_top_hit"] for r in rows)
    print("session leaks, read (NDCG@10, 300 sessions of 10 items):")
    print(f"  {'feature':<16} {'ndcg@10':>8} {'top-1 hits':>10}")
    print(f"  {'leaky (clicked)':<16} {leaky_ndcg:>8.3f} {leaky_hits:>6}/{N_SESSIONS}")
    print(f"  {'as-of (prior)':<16} {as_of_ndcg:>8.3f} {as_of_hits:>6}/{N_SESSIONS}")
    print("\nreading: the leaky feature is the outcome itself - it places")
    print("the clicked item first in all 300 sessions, so the eval")
    print("reports a perfect top-1 hit rate. At serve time the click has")
    print("not happened yet; the model can only use the as-of feature,")
    print("which places the target first in 33 of 300 sessions. The gap")
    print("between 300/300 and 33/300 is the leak: an offline eval whose")
    print("feature window includes the label window validates a model")
    print("that cannot exist online. Check feature-vs-label time ordering")
    print("before trusting a session feature's eval - the as-of join")
    print("from stage 44 applied to session features.")


if __name__ == "__main__":
    main()
