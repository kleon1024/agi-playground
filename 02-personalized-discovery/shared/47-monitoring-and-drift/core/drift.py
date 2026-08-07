"""Monitoring and drift, read: the prediction stayed flat; the world
did not.

Stage 47 introduces online monitoring. Offline evaluation reuses the
same snapshot the model was trained on, so it cannot see a serving-time
break. The online signal that can is the gap between what the model
predicted and what users actually did, tracked per hour.

Run:
    uv run python core/drift.py
"""

from __future__ import annotations

# Hourly rows: predicted CTR stays 0.040; observed CTR falls as a price
# feature silently breaks at hour 5 and returns values of zero.
OBSERVED = [0.039, 0.041, 0.038, 0.040, 0.036, 0.031, 0.028, 0.026, 0.023, 0.021, 0.022, 0.020]


def main() -> None:
    print("monitoring and drift, read (12 hours, predicted ctr 0.040):")
    gap_ewma = 0.0
    alert_streak = 0
    for hour, observed in enumerate(OBSERVED):
        gap = 0.040 - observed
        gap_ewma = 0.7 * gap_ewma + 0.3 * gap
        if gap_ewma > 0.010:
            alert_streak += 1
            flag = " ALERT" if alert_streak >= 3 else ""
        else:
            alert_streak = 0
            flag = ""
        print(f"  hour {hour:>2}: predicted 0.040, observed {observed:.3f}, "
              f"gap {gap:.3f}, ewma {gap_ewma:.3f}{flag}")
    print("\nreading: the model kept predicting 0.040 while users")
    print("clicked less every hour. The offline eval cannot see this -")
    print("its labels come from the same broken world. The prediction-")
    print("observation gap, tracked online, is what catches the")
    print("regression nobody flagged.")


if __name__ == "__main__":
    main()
