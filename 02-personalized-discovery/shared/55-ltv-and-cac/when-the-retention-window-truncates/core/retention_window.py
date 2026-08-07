"""Retention window truncates, read: the observed window decides the
channel verdict.

Stage 55 detour: LTV is measured on an observation window, and the
window truncates the cohort's curve. A fast-decay channel's curve is
fully visible in three months; a slowly-ramping channel's is not - at
three months it looks like a weak channel, and by twenty-four it is
the strongest. A team that reads the truncated window and stops ("count
what we saw") ranks paid installs above referral; the full curve says
the opposite by an order of magnitude. The fix is to model the curve
from recency-frequency data, not to read the window as the truth.

Run:
    uv run python core/retention_window.py
"""

from __future__ import annotations

REVENUE = 5.0
MONTHS = 24

# True 24-month retention curves. Paid installs decays geometrically
# from month one; referral ramps for five months, then stays flat.
CHANNELS = {
    "paid installs": {
        "cac": 8.0,
        "retention": [1.00, 0.28, 0.13, 0.06, 0.03, 0.018, 0.011, 0.006],
    },
    "referral": {
        "cac": 4.0,
        "retention": [0.10, 0.20, 0.32, 0.40, 0.42],
    },
}


def full_curve(name: str) -> list[float]:
    if name == "paid installs":
        out = [1.00, 0.28, 0.13, 0.06, 0.03]
        while len(out) < MONTHS:
            out.append(round(out[-1] * 0.60, 3))
        return out
    out = [0.10, 0.20, 0.32, 0.40, 0.42]
    while len(out) < MONTHS:
        out.append(0.42)
    return out


def ltv(retention: list[float]) -> float:
    return sum(r * REVENUE for r in retention)


def render() -> None:
    print("retention window truncates, read (24-month ltv, $5/month):")
    print(f"  {'channel':<15} {'3-month view':>12} {'true 24m':>9} "
          f"{'3m ltv/cac':>10} {'true ltv/cac':>12}")
    for name in ("paid installs", "referral"):
        true = full_curve(name)
        cac = float(CHANNELS[name]["cac"])
        short = ltv(true[:3])
        full = ltv(true)
        print(
            f"  {name:<15} ${short:>10.2f} ${full:>8.2f} "
            f"{short / cac:>10.2f} {full / cac:>12.2f}"
        )
    print("\nreading: at three months paid installs looks like the better")
    print("bet (0.88 vs 0.78) - its curve is fully visible because it")
    print("decays immediately. Referral looks weak because its users")
    print("ramp slowly; the truncated window sees only the ramp, not the")
    print("flat 0.42 tail, so the 3-month ltv/cac is 0.78 against a true")
    print("11.8. A team that reads the window and stops ranks the wrong")
    print("channel; the fix is to model the curve from recency-frequency")
    print("data instead of reading the truncated window as the truth.")


if __name__ == "__main__":
    render()
