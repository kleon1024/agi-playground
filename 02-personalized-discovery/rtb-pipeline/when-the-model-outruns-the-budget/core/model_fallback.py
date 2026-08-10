"""The model-fallback detour: the 25ms inference slot is a tail, too.

Stage 29's audit shows the total pipeline's p99 blows the 100ms
deadline. This detour isolates the model stage: the heavy inference
model (nominal 25ms slot) has its own heavy tail, and when it runs
long the request cannot win. The fix is a cascade — a fast fallback
model for the requests that arrive at the model stage late. This
script serves 10,000 requests (fixed seed) under two policies:
heavy-model-only, and a cascade that switches to a cheaper model when
the elapsed time before inference is already high.

Run:
    uv run python core/model_fallback.py
"""

from __future__ import annotations

import random
import statistics

N_REQUESTS = 10_000
DEADLINE_MS = 100.0
CUTOFF_MS = 60.0  # elapsed before model entry; above this, fall back

NONMODEL_MEDIAN = 55.0  # parse + profile + context + decision + send
NONMODEL_SIGMA = 0.2
MODEL_A_MEDIAN = 25.0  # heavy model, nominal slot
MODEL_A_SIGMA = 0.5
MODEL_B_MEDIAN = 8.0  # cheap fallback
MODEL_B_SIGMA = 0.3


def percentile(sorted_values: list[float], p: float) -> float:
    return sorted_values[int(p * (len(sorted_values) - 1))]


def main() -> None:
    rng = random.Random(20260808)

    heavy_totals: list[float] = []
    cascade_totals: list[float] = []
    fallback_share = 0
    for _ in range(N_REQUESTS):
        nonmodel = NONMODEL_MEDIAN * (2.71828 ** (NONMODEL_SIGMA * rng.gauss(0, 1)))
        model_a = MODEL_A_MEDIAN * (2.71828 ** (MODEL_A_SIGMA * rng.gauss(0, 1)))
        heavy_totals.append(nonmodel + model_a)

        if nonmodel > CUTOFF_MS:
            model_b = MODEL_B_MEDIAN * (2.71828 ** (MODEL_B_SIGMA * rng.gauss(0, 1)))
            cascade_totals.append(nonmodel + model_b)
            fallback_share += 1
        else:
            cascade_totals.append(nonmodel + model_a)

    def stats(values: list[float]) -> tuple[float, float, float, float, int]:
        s = sorted(values)
        return (
            percentile(s, 0.50),
            percentile(s, 0.95),
            percentile(s, 0.99),
            statistics.mean(values),
            sum(1 for v in values if v > DEADLINE_MS),
        )

    print("model-fallback audit: 10,000 requests, fixed seed")
    print("heavy model median 25ms (sigma 0.5); cheap fallback median")
    print(f"8ms; non-model stages 55ms; deadline {DEADLINE_MS:.0f}ms\n")
    print(f"  {'policy':>14} {'p50':>7} {'p95':>7} {'p99':>7} "
          f"{'mean':>7} {'timeouts':>9}")
    for label, values in (
        ("heavy-only", heavy_totals),
        ("cascade", cascade_totals),
    ):
        p50, p95, p99, mean, to = stats(values)
        print(f"  {label:>14} {p50:>7.1f} {p95:>7.1f} {p99:>7.1f} "
              f"{mean:>7.1f} {to:>6} ({to / N_REQUESTS:>4.1%})")

    print(f"\nfallback share: {fallback_share / N_REQUESTS:.1%} of requests")
    print("served by the cheap model")

    print("\nreading: the model stage is a tail inside the pipeline. The")
    print("heavy model's p99 runs long, and those requests lose the")
    print("deadline. The cascade swaps in the cheap model exactly when")
    print("the request is already late — recovering most timeouts at the")
    print("price of lower bid quality on the worst-tail requests, which")
    print("are also the ones whose data is the least certain.")


if __name__ == "__main__":
    main()
