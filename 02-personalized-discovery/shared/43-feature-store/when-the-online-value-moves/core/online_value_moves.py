"""The store freezes a value at ingestion; the refresh interval decides
how stale the served value gets before the world moves again.

Stage 43's store guarantees that training and serving read the same
frozen number. This detour asks how stale that number is allowed to
become. A fast-moving value - a promo price that drops at hour 2 - is
served at its ingestion-time value until the next refresh. The batch
refresh interval trades freshness against write cost, and streaming
(per-event updates) is the expensive end of the same trade.

Run:
    uv run python core/online_value_moves.py
"""

from __future__ import annotations

# Same score function and catalogue as the stage's store model. P1002's
# price drops during hour 2 (a promo ends), raising its live score from
# -2.5 to 12.5 and moving it above P1003 in the live ranking.
ITEMS = {
    "P1001": {"ctr": 0.032, "price": 49.0},
    "P1002": {"ctr": 0.032, "price": 89.0, "promo_price": 59.0, "promo_hour": 2},
    "P1003": {"ctr": 0.011, "price": 19.0},
    "P1004": {"ctr": 0.025, "price": 39.0},
}
HORIZON = 24


def score(ctr: float, price: float) -> float:
    return 1000.0 * ctr - 0.5 * price + 10.0


def live_price(item_id: str, hour: int) -> float:
    """The world's price during this hour. The change lands mid-hour 2."""
    item = ITEMS[item_id]
    if "promo_hour" in item and hour >= item["promo_hour"]:
        return item["promo_price"]
    return item["price"]


def served_price(item_id: str, hour: int, refresh_hours: int | None) -> float:
    """The price the store serves: frozen at the last refresh instant.

    A refresh at the start of hour r reads the value as of r. A change
    that lands mid-hour 2 is therefore picked up by the first refresh
    running at hour 3 or later; every hour before that serves the old
    frozen value.
    """
    item = ITEMS[item_id]
    if refresh_hours is None:  # streaming: the value updates per event
        return live_price(item_id, hour)
    last_refresh = (hour // refresh_hours) * refresh_hours
    if "promo_hour" in item and last_refresh >= 3:
        return item["promo_price"]
    return item["price"]


def live_order(hour: int) -> list[str]:
    return sorted(
        ITEMS,
        key=lambda i: score(ITEMS[i]["ctr"], live_price(i, hour)),
        reverse=True,
    )


def served_order(hour: int, refresh_hours: int | None) -> list[str]:
    return sorted(
        ITEMS,
        key=lambda i: score(ITEMS[i]["ctr"], served_price(i, hour, refresh_hours)),
        reverse=True,
    )


def wrong_pair_hours(hour: int, refresh_hours: int | None) -> int:
    live_pos = {item: p for p, item in enumerate(live_order(hour))}
    served_pos = {item: p for p, item in enumerate(served_order(hour, refresh_hours))}
    wrong = 0
    ids = list(ITEMS)
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            id_a, id_b = ids[a], ids[b]
            if (live_pos[id_a] < live_pos[id_b]) != (
                served_pos[id_a] < served_pos[id_b]
            ):
                wrong += 1
    return wrong


def main() -> None:
    print("online value moves, read (promo lands at hour 2, horizon 24h):")
    print("  live ranking after hour 2:")
    for p, item_id in enumerate(live_order(3)):
        price = live_price(item_id, 3)
        print(f"    {p + 1}. {item_id} (price ${price:.0f}, score {score(ITEMS[item_id]['ctr'], price):.1f})")
    print()
    print("  refresh        stale hours  wrong pairs  pair-hours")
    for label, refresh in (("1h batch", 1), ("4h batch", 4), ("8h batch", 8), ("24h batch", 24), ("streaming", None)):
        stale = [
            hour
            for hour in range(HORIZON)
            if served_order(hour, refresh) != live_order(hour)
        ]
        pairs = wrong_pair_hours(stale[0], refresh) if stale else 0
        print(f"  {label:<13}  {len(stale):>11}  {pairs:>11}  {len(stale) * pairs:>11}")
    print()
    print("reading: the store's guarantee is identical reads, not current")
    print("reads. With a 24h batch refresh the stale promo price ranks")
    print("P1002 below P1003 for 22 of 24 hours; streaming holds the")
    print("disagreement to zero - the change is served the hour it lands.")
    print("Freshness is a separate")
    print("decision per feature - the store keeps the two decisions from")
    print("colliding, it does not decide the latency class for you.")


if __name__ == "__main__":
    main()
