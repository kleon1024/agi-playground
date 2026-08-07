"""Online feature lags, read: the server serves yesterday's value and
the model is right about a world that ended.

Stage 44 detour: prices update at midnight; the training snapshot was
taken before the update. The estimate uses the logged value while the
user sees the live value.

Run:
    uv run python core/online_lag.py
"""

from __future__ import annotations

ITEMS = [
    {"id": "P1001", "logged_price": 49.0, "live_price": 56.0, "logged_ctr": 0.042},
    {"id": "P1002", "logged_price": 89.0, "live_price": 89.0, "logged_ctr": 0.023},
    {"id": "P1003", "logged_price": 19.0, "live_price": 24.0, "logged_ctr": 0.018},
]


def live_ctr(price: float) -> float:
    if price <= 20.0:
        return 0.018
    if price <= 30.0:
        return 0.030
    if price <= 55.0:
        return 0.042
    return 0.026


def main() -> None:
    print("online feature lags, read (stale estimate vs live reality):")
    print("  item   logged price  live price  logged ctr  live ctr")
    for item in ITEMS:
        print(f"  {item['id']}   ${item['logged_price']:<10.0f} "
              f"${item['live_price']:<10.0f} {item['logged_ctr']:.3f}      "
              f"{live_ctr(item['live_price']):.3f}")
    print("\nreading: P1001 and P1003 changed price after the snapshot;")
    print("their logged CTRs describe the old prices. The estimate is")
    print("not wrong - it is stale. The lag between the snapshot and")
    print("the live value is the skew, and it is a pipeline property,")
    print("not a model one.")


if __name__ == "__main__":
    main()
