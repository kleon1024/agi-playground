"""Policy borrows luck, read: the log measures quality under the
policy, not quality.

Stage 45 detour: exposure bias. Two items convert at the same true
rate, but one was served in a featured slot that doubles clicks and
the other in a low position that halves them. The naive log estimate
calls the featured item twice as good. Inverse propensity weighting
recovers the true rate when the propensities are the ones that
produced the log - and reproduces the bias when the policy changed and
the stored propensities went stale.

Run:
    uv run python core/policy_luck.py
"""

from __future__ import annotations

# 200 impressions per item; position multiplier acts on the true CTR.
ROWS = [
    {"id": "A", "impressions": 200, "multiplier": 2.0, "true_ctr": 0.030},
    {"id": "B", "impressions": 200, "multiplier": 0.5, "true_ctr": 0.030},
]


def clicks(row: dict[str, float | str]) -> int:
    return round(float(row["impressions"]) * float(row["true_ctr"]) * float(row["multiplier"]))


def naive(row: dict[str, float | str]) -> float:
    return clicks(row) / float(row["impressions"])


def ips(row: dict[str, float | str], propensity: float) -> float:
    """Inverse-propensity estimate: weight each click by 1/p."""
    return clicks(row) * (1.0 / propensity) / float(row["impressions"])


def main() -> None:
    print("policy borrows luck, read (200 impressions each, true ctr 0.030):")
    print("  item  multiplier  clicks  naive ctr  IPS (true)  IPS (stale)")
    for row in ROWS:
        true_p = float(row["multiplier"])  # propensity that produced the log
        stale_p = 1.0  # policy changed; stored propensities no longer apply
        print(
            f"  {row['id']}       {row['multiplier']:.1f}      "
            f"{clicks(row):>3}    {naive(row):.3f}      "
            f"{ips(row, true_p):.3f}       {ips(row, stale_p):.3f}"
        )
    print("\nreading: the naive log says A converts at 0.060 and B at 0.015")
    print("- A borrowed the featured slot's luck. IPS with the propensities")
    print("that produced the log returns 0.030 for both. When the policy")
    print("changes and the stored propensities go stale, the correction")
    print("reproduces the bias - the loop's luck is only payable with the")
    print("propensity log, which is why exploration must be logged, not")
    print("assumed.")


if __name__ == "__main__":
    main()
