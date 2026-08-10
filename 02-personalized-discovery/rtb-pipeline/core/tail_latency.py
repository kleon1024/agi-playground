"""The tail-latency audit: the p95 fits the deadline, the p99 does not.

Stage 29 splits a 100ms budget across six pipeline stages. The audit
asks the case-finding question at production scale: what does the
deadline actually see? It draws 20,000 requests (fixed seed) where
each stage's latency is lognormal with the stage's nominal time as the
median and a declared spread, sums them, and reads the total against
the 100ms deadline.

Run:
    uv run python core/tail_latency.py
"""

from __future__ import annotations

import random
import statistics

N_REQUESTS = 20_000
DEADLINE_MS = 100.0
SIGMA = 0.25

# (stage name, nominal ms) from the stage's budget split.
STAGES = [
    ("request parse", 5.0),
    ("user profile lookup", 20.0),
    ("context features", 10.0),
    ("model inference", 25.0),
    ("bid decision", 15.0),
    ("response send", 5.0),
]


def percentile(sorted_values: list[float], p: float) -> float:
    idx = int(p * (len(sorted_values) - 1))
    return sorted_values[idx]


def main() -> None:
    rng = random.Random(20260808)

    stage_samples: list[list[float]] = [[] for _ in STAGES]
    totals: list[float] = []
    for _ in range(N_REQUESTS):
        total = 0.0
        for i, (_, nominal) in enumerate(STAGES):
            latency = nominal * (2.71828 ** (SIGMA * rng.gauss(0, 1)))
            stage_samples[i].append(latency)
            total += latency
        totals.append(total)

    print("tail-latency audit: 20,000 requests, fixed seed")
    print(f"six stages, lognormal latency with declared spread sigma {SIGMA}\n")
    print(f"  {'stage':>22} {'p50':>7} {'p90':>7} {'p99':>7}")
    for (name, _), samples in zip(STAGES, stage_samples):
        s = sorted(samples)
        print(f"  {name:>22} {percentile(s, 0.50):>7.1f} "
              f"{percentile(s, 0.90):>7.1f} {percentile(s, 0.99):>7.1f}")

    t = sorted(totals)
    print("\n  total vs 100ms deadline:")
    print(f"    p50:  {percentile(t, 0.50):.1f} ms")
    print(f"    p90:  {percentile(t, 0.90):.1f} ms")
    print(f"    p95:  {percentile(t, 0.95):.1f} ms")
    print(f"    p99:  {percentile(t, 0.99):.1f} ms")
    timed_out = sum(1 for x in totals if x > DEADLINE_MS)
    print(f"    mean: {statistics.mean(totals):.1f} ms")
    print(f"    timed out (>{DEADLINE_MS:.0f} ms): "
          f"{timed_out} ({timed_out / N_REQUESTS:.1%})")

    print("\nreading: the p50 total sits near the nominal 80 ms and the")
    print("p95 fits inside the 20 ms margin — but the p99 blows the")
    print("deadline, and every one of those requests is a slot with no")
    print("bid. Averaging the pipeline hides it: the mean is fine, the")
    print("deadline is a tail constraint, and the margin has to be")
    print("sized for the p99, not the p95.")


if __name__ == "__main__":
    main()
