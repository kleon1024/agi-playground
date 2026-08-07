"""Real-time user state, read: the session is a feature the batch model
cannot see.

Stage 48 introduces real-time personalization. The batch ranker scores
an item from learned priors. The session carries what this user did
minutes ago - viewed a category, dwelled on an item - and that state
can re-rank the slate before the batch model would ever be retrained.

Run:
    uv run python core/session_state.py
    uv run python core/session_state.py --emit-log /tmp/session-envelope.json

The `--emit-log` flag writes a session-cohort simulation stratified by
session depth so the production path in `prod/session_audit.py` can
answer the case-finding question of the stage: the aggregate realtime
lift is a blend, and the blend is carried by the deep sessions that own
the least traffic.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

CATALOGUE = [
    {"id": "P1001", "category": "audio", "ctr": 0.032},
    {"id": "P1002", "category": "audio", "ctr": 0.030},
    {"id": "P1003", "category": "cable", "ctr": 0.028},
    {"id": "P1004", "category": "cable", "ctr": 0.025},
    {"id": "P1005", "category": "cases", "ctr": 0.020},
    {"id": "P1006", "category": "cases", "ctr": 0.018},
]

# The user just viewed P1001 (audio) with a long dwell.
LAST_VIEW = "P1001"
LAST_VIEW_MINS = 3
CATEGORY_BOOST = 0.012

# Cohort simulation catalogue: three categories, five items each, with a
# gap between categories so the boost changes the served slate. A user
# clicks an item at its category rate when the category matches their
# interest, and at 30% of that rate otherwise.
COHORT_CATALOGUE = {
    "audio": [0.032, 0.031, 0.030, 0.029, 0.028],
    "cable": [0.026, 0.025, 0.024, 0.023, 0.022],
    "cases": [0.020, 0.019, 0.018, 0.017, 0.016],
}
CATEGORIES = list(COHORT_CATALOGUE)

# The dwelled category matches the user's true interest with probability
# q(depth). Depth 0 has no session state: the realtime policy is
# identical to the batch one. A single dwell is close to a coin flip;
# the signal sharpens as the session accumulates evidence.
DEPTHS = [
    {"depth": 0, "q": 0.0, "traffic": 0.00},
    {"depth": 1, "q": 0.50, "traffic": 0.70},
    {"depth": 2, "q": 0.85, "traffic": 0.20},
    {"depth": 4, "q": 0.95, "traffic": 0.10},
]
N_SESSIONS = 400
SLATE = 5


def batch_score(item: dict[str, object]) -> float:
    return float(item["ctr"])


def realtime_score(item: dict[str, object]) -> float:
    score = batch_score(item)
    if item["category"] == "audio":
        decay = CATEGORY_BOOST * (0.9 ** LAST_VIEW_MINS)
        score += decay
    return score


def cohort_items() -> list[tuple[str, float]]:
    """(category, ctr) pairs for the cohort catalogue."""
    items: list[tuple[str, float]] = []
    for category, ctrs in COHORT_CATALOGUE.items():
        items.extend((category, ctr) for ctr in ctrs)
    return items


def served_ctr(
    interest: str,
    dwelled: str | None,
) -> tuple[float, float]:
    """Batch and realtime served CTR for one session."""
    items = cohort_items()
    batch = sorted(items, key=lambda item: item[1], reverse=True)[:SLATE]
    if dwelled is None:
        realtime = batch
    else:
        realtime = sorted(
            items,
            key=lambda item: item[1] + (0.010 if item[0] == dwelled else 0.0),
            reverse=True,
        )[:SLATE]

    def expected(slate: list[tuple[str, float]]) -> float:
        total = 0.0
        for category, ctr in slate:
            rate = ctr if category == interest else 0.3 * ctr
            total += rate
        return total / len(slate)

    batch_rate = expected(batch)
    realtime_rate = expected(realtime)
    return batch_rate, realtime_rate


def cohort_simulation() -> list[dict[str, object]]:
    """Per-depth rows: mean batch/realtime CTR and the lift."""
    rng = random.Random(7)
    rows: list[dict[str, object]] = []
    # The same interest category for every depth: the only thing that
    # varies between rows is the signal quality q and the traffic share.
    interest = CATEGORIES[1]
    for entry in DEPTHS:
        depth = entry["depth"]
        q = entry["q"]
        batch_total = 0.0
        realtime_total = 0.0
        for _ in range(N_SESSIONS):
            dwelled: str | None = None
            if depth > 0:
                dwelled = interest if rng.random() < q else rng.choice(
                    [c for c in CATEGORIES if c != interest]
                )
            batch_rate, realtime_rate = served_ctr(interest, dwelled)
            batch_total += batch_rate
            realtime_total += realtime_rate
        batch_mean = batch_total / N_SESSIONS
        realtime_mean = realtime_total / N_SESSIONS
        rows.append(
            {
                "depth": depth,
                "q": q,
                "traffic": entry["traffic"],
                "batch_ctr": round(batch_mean, 4),
                "realtime_ctr": round(realtime_mean, 4),
                "lift": round(realtime_mean - batch_mean, 4),
            }
        )
    return rows


def render_cohort(rows: list[dict[str, object]]) -> None:
    print("\nsession cohort view (served CTR, batch vs realtime):")
    print(f"  {'depth':>5} {'signal q':>8} {'traffic':>8}  {'batch':>6} "
          f"{'realtime':>9} {'lift':>6}")
    for row in rows:
        print(
            f"  {row['depth']:>5} {row['q']:>8.2f} {row['traffic']:>8.0%}  "
            f"{row['batch_ctr']:.4f} {row['realtime_ctr']:.4f} "
            f"{row['lift']:+.4f}"
        )
    weighted = sum(
        float(row["lift"]) * float(row["traffic"]) for row in rows
    )
    deep = next(r for r in rows if r["depth"] == 4)
    print(f"\n  traffic-weighted lift: {weighted:+.4f} "
          f"(deep-session lift {deep['lift']:+.4f})")
    print("\n  reading: the boost pays, but the per-session payment")
    print("  grows with depth. Depth 1 - a single dwell, the majority")
    print("  of sessions - earns about half the deep-session lift, and")
    print("  the cost is paid per request for every session. The blend")
    print("  hides the ROI difference; stratify before sizing the")
    print("  realtime feature spend.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-log", help="write the cohort rows as JSON")
    args = parser.parse_args()
    print("real-time user state, read (user dwelled 40s on P1001, 3 min ago):")
    print("  batch order (learned ctr):")
    batch = sorted(CATALOGUE, key=batch_score, reverse=True)
    for rank, item in enumerate(batch, start=1):
        print(f"    {rank}. {item['id']} ({item['category']}, ctr {item['ctr']:.3f})")
    print("  realtime order (session boost):")
    realtime = sorted(CATALOGUE, key=realtime_score, reverse=True)
    for rank, item in enumerate(realtime, start=1):
        print(f"    {rank}. {item['id']} ({item['category']}, "
              f"score {realtime_score(item):.3f})")
    print("\nreading: the session pulled audio up and cases down.")
    print("The batch model would need a retrain to learn what the")
    print("session knows from one dwell. The trade is freshness of")
    print("state against the cost of computing it per request.")
    rows = cohort_simulation()
    render_cohort(rows)
    if args.emit_log:
        Path(args.emit_log).write_text(
            json.dumps({"cohorts": rows, "n_sessions": N_SESSIONS, "slate": SLATE})
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
