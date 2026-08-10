"""Peak hits, read: a calendar retrain misses the spike; an error
trigger does not.

Stage 46 detour: retraining cadence is a resource decision, and the
when matters as much as the count. Two schedulers with the same number
of retrains serve a demand spike (hours 8-12) differently: the calendar
retrains on schedule (hours 0 and 12), the error trigger retrains the
first hour the measured rank error crosses its budget (hours 8 and 13).
The calendar serves the stale order for every spike hour and again after
the spike ends; the trigger recovers one hour after each world change.

Run:
    uv run python core/peak_hits.py
"""

from __future__ import annotations

# Fixed rates before the spike; the volatile cohort is boosted during
# hours 8-12, then the world snaps back.
ITEMS = [
    {"id": "P1001", "cohort": "volatile", "base": 0.045},
    {"id": "P1002", "cohort": "volatile", "base": 0.042},
    {"id": "P1003", "cohort": "stable", "base": 0.040},
    {"id": "P1004", "cohort": "volatile", "base": 0.037},
    {"id": "P1005", "cohort": "volatile", "base": 0.035},
    {"id": "P1006", "cohort": "stable", "base": 0.033},
]

SPIKE_HOURS = set(range(8, 13))
SPIKE_BOOST = 0.012
BUDGET = 1  # retrain when more than this many pairs rank wrong
EVAL_HOURS = list(range(15))


def rate(item: dict[str, object], hour: int) -> float:
    boost = SPIKE_BOOST if hour in SPIKE_HOURS and item["cohort"] == "volatile" else 0.0
    return float(item["base"]) + boost


def order_at(hour: int) -> list[str]:
    return [i["id"] for i in sorted(ITEMS, key=lambda i: rate(i, hour), reverse=True)]


def wrong_pairs(model_hour: int, truth_hour: int) -> int:
    model_pos = {item_id: p for p, item_id in enumerate(order_at(model_hour))}
    truth_pos = {item_id: p for p, item_id in enumerate(order_at(truth_hour))}
    ids = [i["id"] for i in ITEMS]
    errors = 0
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            id_a, id_b = ids[a], ids[b]
            if (model_pos[id_a] < model_pos[id_b]) != (truth_pos[id_a] < truth_pos[id_b]):
                errors += 1
    return errors


def calendar_run() -> tuple[list[int], list[int]]:
    """Retrain every 12 hours starting at hour 0."""
    errors: list[int] = []
    retrain_hours: list[int] = [0]
    snapshot = 0
    for hour in EVAL_HOURS:
        if hour in (12,):
            snapshot = hour
            retrain_hours.append(hour)
        errors.append(wrong_pairs(snapshot, hour))
    return errors, retrain_hours


def adaptive_run() -> tuple[list[int], list[int]]:
    """Retrain the hour the measured error crosses the budget."""
    errors: list[int] = []
    retrain_hours: list[int] = [0]
    snapshot = 0
    for hour in EVAL_HOURS:
        error = wrong_pairs(snapshot, hour)
        errors.append(error)
        if error > BUDGET:
            snapshot = hour
            retrain_hours.append(hour)
    return errors, retrain_hours


def main() -> None:
    calendar_errors, calendar_retrains = calendar_run()
    adaptive_errors, adaptive_retrains = adaptive_run()
    print("peak hits, read (spike hours 8-12, retrain when >1 pair wrong):")
    print("  hour  calendar  adaptive")
    for hour, (c, a) in enumerate(zip(calendar_errors, adaptive_errors)):
        flag_c = " R" if hour in calendar_retrains else ""
        flag_a = " R" if hour in adaptive_retrains else ""
        print(f"  {hour:>3}   {c:>5}   {a:>7}{flag_c:<2}{flag_a:<2}")
    cal_peak = max(calendar_errors)
    ada_peak = max(adaptive_errors)
    cal_er = sum(calendar_errors)
    ada_er = sum(adaptive_errors)
    print()
    print(f"  retrains:     calendar {len(calendar_retrains)}, "
          f"adaptive {len(adaptive_retrains)}")
    print(f"  error-hours:  calendar {cal_er}, adaptive {ada_er}")
    print(f"  peak error:   calendar {cal_peak}, adaptive {ada_peak}")
    print("\nreading: the calendar retrained at hour 12, mid-spike, so it")
    print("served the stale order for every spike hour and again after the")
    print("spike ended. The trigger spent one extra retrain on the first")
    print("hour each world change became measurable and cut stale exposure")
    print("threefold. The retraining decision is the when, not the count -")
    print("a fixed cadence spends its budget on the calendar, an error")
    print("trigger spends it on the world.")


if __name__ == "__main__":
    main()
