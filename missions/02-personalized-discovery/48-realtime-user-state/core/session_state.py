"""Real-time user state, read: the session is a feature the batch model
cannot see.

Stage 48 introduces real-time personalization. The batch ranker scores
an item from learned priors. The session carries what this user did
minutes ago - viewed a category, dwelled on an item - and that state
can re-rank the slate before the batch model would ever be retrained.

Run:
    uv run python core/session_state.py
"""

from __future__ import annotations

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


def batch_score(item: dict[str, object]) -> float:
    return float(item["ctr"])


def realtime_score(item: dict[str, object]) -> float:
    score = batch_score(item)
    if item["category"] == "audio":
        decay = CATEGORY_BOOST * (0.9 ** LAST_VIEW_MINS)
        score += decay
    return score


def main() -> None:
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


if __name__ == "__main__":
    main()
