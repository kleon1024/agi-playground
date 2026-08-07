"""Slice hides, read: the aggregate hides the slice, and the slice's
own noise hides the fix.

Stage 47 detour: the slice panel finds a collapse the aggregate
cannot see - and immediately runs into the second failure: the small
segment's daily signal is noise. A 500-impression-a-day slice with a
real 50% drop looks like a coin flip day to day, so a daily test
either waits for a noisy low day or fires on pre-drop noise. The fix
is pooling or shrinkage, and the price is detection latency.

Run:
    uv run python core/slice_hides.py
"""

from __future__ import annotations

import math
import random

# Segment sizes in impressions per day; true CTR drops 50% at day 10.
SEGMENTS = [
    {"name": "50k/day", "impressions": 50_000},
    {"name": "5k/day", "impressions": 5_000},
    {"name": "500/day", "impressions": 500},
]

PRE_CTR = 0.040
POST_CTR = 0.020
DROP_DAY = 10
DAYS = 30
ALPHA = 1.96  # two-sided 5%
POOL_DAYS = 14


def simulate() -> dict[str, dict[str, object]]:
    rng = random.Random(18)
    out: dict[str, dict[str, object]] = {}
    for segment in SEGMENTS:
        n = segment["impressions"]
        sd = math.sqrt(PRE_CTR * (1 - PRE_CTR) / n)
        observed = []
        for day in range(DAYS):
            true = POST_CTR if day >= DROP_DAY else PRE_CTR
            observed.append(max(0.0, true + rng.gauss(0.0, sd)))
        out[segment["name"]] = {"sd": sd, "observed": observed}
    return out


def daily_check(observed: list[float], sd: float) -> tuple[int, int]:
    """First post-drop flag day and pre-drop false alarms."""
    false_alarms = 0
    detection = -1
    for day, value in enumerate(observed):
        if abs(value - PRE_CTR) / sd > ALPHA:
            if day < DROP_DAY:
                false_alarms += 1
            elif detection < 0:
                detection = day
    return detection, false_alarms


def pooled_check(observed: list[float], sd: float) -> tuple[int, int]:
    """14-day rolling mean test: detection when a full post-drop window."""
    pooled_sd = sd / math.sqrt(POOL_DAYS)
    false_alarms = 0
    detection = -1
    for day in range(POOL_DAYS - 1, DAYS):
        window = observed[day - POOL_DAYS + 1 : day + 1]
        mean = sum(window) / POOL_DAYS
        if abs(mean - PRE_CTR) / pooled_sd > ALPHA:
            if day < DROP_DAY:
                false_alarms += 1
            elif day >= DROP_DAY + POOL_DAYS - 1 and detection < 0:
                detection = day
    return detection, false_alarms


def main() -> None:
    results = simulate()
    print("slice hides, read (true ctr drops 0.040 -> 0.020 at day 10):")
    print(f"  {'segment':<10} {'daily sd':>8}  {'daily detect':>12}  "
          f"{'daily false':>11}  {'pooled 14d':>10}  {'pooled false':>12}")
    for segment in SEGMENTS:
        data = results[segment["name"]]
        sd = data["sd"]
        observed = data["observed"]
        d_day, d_false = daily_check(observed, sd)
        p_day, p_false = pooled_check(observed, sd)
        daily_detect = f"day {d_day}" if d_day >= 0 else "never"
        pooled_detect = f"day {p_day}" if p_day >= 0 else "never"
        print(
            f"  {segment['name']:<10} {sd:.5f}  "
            f"{daily_detect:>12}  "
            f"{d_false:>11}  "
            f"{pooled_detect:>10}  "
            f"{p_false:>12}"
        )
    print("\nreading: the 500/day slice is where the drop lives and where")
    print("the signal is noisiest - a daily test fires on pre-drop noise or")
    print("waits for a lucky low day, while the pooled window detects")
    print("reliably only after 14 days of post-drop evidence. On a small")
    print("slice you cannot have both low false alarms and fast detection;")
    print("the fix is pooling or shrinkage, not a tighter threshold.")


if __name__ == "__main__":
    main()
