"""Alert is noisy, read: a threshold tight enough to catch a real
break is tight enough to fire on noise.

Stage 47 detour: observed CTR jitters around the prediction. A tight
threshold flags the jitter; a loose one misses the break until it is
deep. The threshold is a trade between time-to-detection and false
alarms, and it must be set on the noise, not on hope.

Run:
    uv run python core/noisy_alert.py
"""

from __future__ import annotations

# Hourly observed CTR: jitter around 0.040 until hour 8, then a break.
OBSERVED = [
    0.041, 0.039, 0.042, 0.038, 0.040, 0.041,
    0.039, 0.042, 0.031, 0.026, 0.023, 0.021,
]


def alert_hours(threshold: float) -> list[int]:
    out = []
    for hour, obs in enumerate(OBSERVED):
        if abs(0.040 - obs) > threshold:
            out.append(hour)
    return out


def main() -> None:
    print("alert is noisy, read (predicted ctr 0.040, break at hour 8):")
    for threshold in (0.002, 0.005, 0.010):
        hours = alert_hours(threshold)
        print(f"  threshold +/-{threshold:.3f}: alerts at hours {hours}")
    print("\nreading: at +/-0.002 the panel fires on seven hours of noise;")
    print("at +/-0.010 it waits until the break is unmistakable. The")
    print("threshold is a decision about what a false alarm costs and")
    print("how fast a real break must be caught - it cannot be both")
    print("tight and quiet.")


if __name__ == "__main__":
    main()
