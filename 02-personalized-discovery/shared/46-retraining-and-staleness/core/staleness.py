"""Staleness and retraining, read: the model trained at hour 0 ranks
the world as it was at hour 0.

Stage 46 introduces staleness. Item click rates drift over time; the
model holds the snapshot it was trained on. Rank error against the
current truth grows with the age of the snapshot, and retraining on a
newer snapshot buys it back.

Run:
    uv run python core/staleness.py
"""

from __future__ import annotations

ITEMS = [
    {"id": "P1001", "base": 0.045, "trend": 0.0012},
    {"id": "P1002", "base": 0.042, "trend": -0.0008},
    {"id": "P1003", "base": 0.040, "trend": 0.0004},
    {"id": "P1004", "base": 0.037, "trend": -0.0010},
    {"id": "P1005", "base": 0.035, "trend": 0.0018},
    {"id": "P1006", "base": 0.033, "trend": 0.0000},
]


def ctr_at(item: dict[str, float], hour: int) -> float:
    return item["base"] + item["trend"] * hour


def rank_error(model_hour: int, truth_hour: int) -> int:
    """Number of pairwise orderings the snapshot model gets wrong."""
    model_order = sorted(
        ITEMS, key=lambda i: ctr_at(i, model_hour), reverse=True
    )
    truth_order = sorted(
        ITEMS, key=lambda i: ctr_at(i, truth_hour), reverse=True
    )
    model_pos = {i["id"]: p for p, i in enumerate(model_order)}
    truth_pos = {i["id"]: p for p, i in enumerate(truth_order)}
    errors = 0
    for a in range(len(ITEMS)):
        for b in range(a + 1, len(ITEMS)):
            id_a, id_b = ITEMS[a]["id"], ITEMS[b]["id"]
            if (model_pos[id_a] < model_pos[id_b]) != (truth_pos[id_a] < truth_pos[id_b]):
                errors += 1
    return errors


def main() -> None:
    print("staleness, read (pairwise rank errors vs the truth at hour h):")
    print("  snapshot from hour 0 evaluated at hour h:")
    for hour in (0, 6, 12):
        print(f"    hour {hour:>2}: {rank_error(0, hour)} wrong pairs")
    print("  snapshot from hour 6 evaluated at hour 12:")
    print(f"    hour 12: {rank_error(6, 12)} wrong pairs")
    print("\nreading: rank error grows from 0 at hour 0 to several")
    print("wrong pairs at hour 12. A snapshot from hour 6 cuts that")
    print("error to a single pair.")
    print("The question is not whether to retrain - the world moves -")
    print("but how to notice that the snapshot has stopped paying.")


if __name__ == "__main__":
    main()
