"""A staged funnel, timed end to end, to answer one question: does a p95
target on the whole request equal the sum of p95 targets on each stage?

Every stage before this one in the mission -- recall, pre-rank, fine-rank,
the value tree -- was allowed to run as long as it needed to produce a
correct answer. Serving removes that freedom: the whole funnel has to
complete inside one request, and the mission states a p95 latency target,
not a mean. This file builds the smallest thing that can be wrong about that
question -- a simulated six-stage pipeline with a real timing harness -- runs
it thousands of times, and measures whether "add up each stage's p95" agrees
with the actual end-to-end p95.

It does not. The reason is not a quirk of this simulation: a request's total
latency is high only when *its own* draws from each stage happen to be slow,
and it is very unlikely that every stage is simultaneously having a bad day
on the same request. Summing each stage's own 95th percentile assumes exactly
that coincidence, so it overestimates the truth -- except for the one stage
this file also lets you break: recall's multi-queue fan-out, which is a
`max` over queues rather than a `sum`, and which timeouts can cap even
further.

Two ways to spend a latency budget are demonstrated here, not asserted:

* **Do less work.** Shrinking the candidate set a stage has to score (fewer
  candidates into pre-rank, fewer into fine-rank) shrinks that stage's own
  distribution directly.
* **Do the work in parallel.** Recall's four queues run one at a time in
  `serial` mode (cost: their sum) or concurrently in `parallel` mode (cost:
  the slowest one, or the timeout, whichever is smaller). The union of
  queues costs what the slowest surviving queue costs, not what all four
  cost added together.

A cache stage in front of the whole funnel demonstrates a third, separate
effect: a cache that is hit most of the time collapses the *mean* almost in
proportion to its hit rate, but barely touches the *p95*, because the 95th
percentile of request latency is disproportionately made of the requests
that missed the cache and paid full price. A latency number bought by adding
a cache and read off the mean is not the number the p95 target cares about.

All per-stage costs below are lognormal draws with disclosed, tuned
parameters (see `STAGE_SPECS` and `RECALL_QUEUES`) -- chosen so that the tail
is visibly heavier than the median, which is the one property real service
latencies reliably share, and so the composition effects above show up
clearly rather than being washed out by nearly-symmetric noise. They are not
a claim about any real service's latency in milliseconds. What is measured
for real is the arithmetic of composition: the shape holds regardless of
which specific numbers you tune it to. See `runs/` for the recorded output of
actually executing this file, and the README's evidence boundary for what
that output does and does not establish.

Run:  python latency_pipeline.py --recall-mode parallel --trials 5000
"""

from __future__ import annotations

import argparse
import math
import random
import statistics
from dataclasses import dataclass, field

# --- 1. per-stage cost model --------------------------------------------------
#
# Every stage's latency is a lognormal draw: exp(mu + sigma * z). Lognormal is
# used, not Gaussian, because it cannot go negative and it produces a heavier
# right tail at the same median -- the one qualitative property service
# latencies actually have, and the reason a mean is a bad summary of them.
# `median_ms` and `sigma` were tuned so that no single stage's tail already
# dominates the funnel before you touch any control; if it did, the
# composition question this file exists to demonstrate would already be
# decided by one stage and the rest of the pipeline would be scenery.


def lognormal_ms(rng: random.Random, median_ms: float, sigma: float) -> float:
    mu = math.log(max(median_ms, 1e-6))
    return math.exp(rng.gauss(mu, sigma))


@dataclass(frozen=True)
class QueueSpec:
    name: str
    median_ms: float
    sigma: float


# One queue (item_to_item) is deliberately the slow, heavy-tailed one -- a
# graph traversal over a user's history items, versus a single vector lookup
# or an inverted index probe for the others. That asymmetry is what makes
# `serial` vs `parallel` recall a real difference rather than a wash.
RECALL_QUEUES: tuple[QueueSpec, ...] = (
    QueueSpec("two_tower", median_ms=10.0, sigma=0.25),
    QueueSpec("lexical", median_ms=7.0, sigma=0.20),
    QueueSpec("item_to_item", median_ms=14.0, sigma=0.55),
    QueueSpec("freshness", median_ms=5.0, sigma=0.15),
)


@dataclass(frozen=True)
class StageSpec:
    name: str
    fixed_ms: float          # per-request overhead independent of candidate count
    per_candidate_us: float  # marginal cost per candidate scored, in microseconds
    sigma: float


# Fixed and per-candidate costs are illustrative, not measured off a real
# ranker -- fine_rank's per-candidate cost is set an order of magnitude above
# pre_rank's, which is the entire justification the mission gives for having
# both stages: a model too expensive to run on the full candidate set, run
# only after a cheaper model has done the cutting.
STAGE_SPECS: dict[str, StageSpec] = {
    "pre_rank": StageSpec("pre_rank", fixed_ms=1.0, per_candidate_us=1.2, sigma=0.20),
    "fine_rank": StageSpec("fine_rank", fixed_ms=2.0, per_candidate_us=14.0, sigma=0.25),
    "value_tree": StageSpec("value_tree", fixed_ms=0.5, per_candidate_us=0.3, sigma=0.15),
    "mixing": StageSpec("mixing", fixed_ms=1.5, per_candidate_us=2.5, sigma=0.20),
    "rules": StageSpec("rules", fixed_ms=0.5, per_candidate_us=0.2, sigma=0.15),
}


def staged_latency_ms(rng: random.Random, spec: StageSpec, n_candidates: int) -> float:
    median = spec.fixed_ms + spec.per_candidate_us * n_candidates / 1000.0
    return lognormal_ms(rng, median, spec.sigma)


# --- 2. recall: the one stage with a real serial-vs-parallel choice ----------


@dataclass
class RecallOutcome:
    latency_ms: float
    queues_completed: int
    queues_dropped: int


def recall_latency(
    rng: random.Random, mode: str, timeout_ms: float | None
) -> RecallOutcome:
    """Fan out to every queue; the union costs what the slowest survivor costs.

    `serial`: queues run one after another -- total cost is their sum, because
    nothing about a for-loop lets two network calls overlap in wall-clock time.

    `parallel`: queues run concurrently -- total cost is the slowest queue's
    draw, because the request is only as done as its slowest still-running
    piece. `timeout_ms`, if set, caps that wait: any queue slower than the
    timeout is dropped from the union rather than blocking the request, which
    is what turns a slow straggler into a slightly smaller candidate set
    instead of a slow (or failed) response.
    """
    draws = [lognormal_ms(rng, q.median_ms, q.sigma) for q in RECALL_QUEUES]

    if mode == "serial":
        return RecallOutcome(latency_ms=sum(draws), queues_completed=len(draws), queues_dropped=0)

    if mode != "parallel":
        raise ValueError(f"unknown recall mode: {mode!r}")

    if timeout_ms is None:
        return RecallOutcome(latency_ms=max(draws), queues_completed=len(draws), queues_dropped=0)

    completed = [d for d in draws if d <= timeout_ms]
    dropped = len(draws) - len(completed)
    # The request waits for the slowest *surviving* queue, or the timeout
    # itself if every queue is still outstanding when it fires.
    latency = max(completed) if completed else timeout_ms
    return RecallOutcome(latency_ms=latency, queues_completed=len(completed), queues_dropped=dropped)


# --- 3. one full request through the funnel ----------------------------------


@dataclass
class FunnelConfig:
    recall_mode: str = "parallel"
    recall_timeout_ms: float | None = None
    recall_candidates: int = 3000    # union size handed to pre-rank
    prerank_candidates: int = 300    # cut handed to fine-rank
    finerank_candidates: int = 50    # cut handed to the value tree / mixing / rules
    cache_hit_rate: float = 0.0      # fraction of requests a slate cache answers directly


@dataclass
class RequestTrace:
    stage_ms: dict[str, float] = field(default_factory=dict)
    queues_dropped: int = 0
    cache_hit: bool = False

    @property
    def total_ms(self) -> float:
        return sum(self.stage_ms.values())


def run_request(rng: random.Random, cfg: FunnelConfig) -> RequestTrace:
    trace = RequestTrace()

    if cfg.cache_hit_rate > 0 and rng.random() < cfg.cache_hit_rate:
        # A cache hit skips the entire funnel below it -- this is what makes
        # the cache's effect on the mean so much larger than its effect on
        # the p95: it removes cheap, already-fast requests from the mix, not
        # the slow ones the p95 is measuring.
        trace.stage_ms["cache_hit"] = lognormal_ms(rng, median_ms=1.0, sigma=0.10)
        trace.cache_hit = True
        return trace

    if cfg.cache_hit_rate > 0:
        trace.stage_ms["cache_miss_lookup"] = lognormal_ms(rng, median_ms=0.5, sigma=0.10)

    recall = recall_latency(rng, cfg.recall_mode, cfg.recall_timeout_ms)
    trace.stage_ms["recall"] = recall.latency_ms
    trace.queues_dropped = recall.queues_dropped

    trace.stage_ms["pre_rank"] = staged_latency_ms(rng, STAGE_SPECS["pre_rank"], cfg.recall_candidates)
    trace.stage_ms["fine_rank"] = staged_latency_ms(rng, STAGE_SPECS["fine_rank"], cfg.prerank_candidates)
    trace.stage_ms["value_tree"] = staged_latency_ms(rng, STAGE_SPECS["value_tree"], cfg.finerank_candidates)
    trace.stage_ms["mixing"] = staged_latency_ms(rng, STAGE_SPECS["mixing"], cfg.finerank_candidates)
    trace.stage_ms["rules"] = staged_latency_ms(rng, STAGE_SPECS["rules"], cfg.finerank_candidates)
    return trace


# --- 4. the harness: run it many times, measure the composition -------------


def percentile(values: list[float], p: float) -> float:
    """p in (0, 100). statistics.quantiles with n=1000 gives 0.1-percentile
    resolution, which is finer than we need but avoids picking an n that
    happens to land exactly on p=95 and hiding interpolation error."""
    if len(values) < 2:
        return values[0] if values else float("nan")
    qs = statistics.quantiles(values, n=1000, method="inclusive")
    idx = min(max(round(p * 10) - 1, 0), len(qs) - 1)
    return qs[idx]


def run_harness(cfg: FunnelConfig, trials: int, seed: int) -> dict:
    rng = random.Random(seed)
    totals: list[float] = []
    per_stage: dict[str, list[float]] = {}
    cache_hits = 0
    total_dropped_queues = 0

    for _ in range(trials):
        trace = run_request(rng, cfg)
        totals.append(trace.total_ms)
        if trace.cache_hit:
            cache_hits += 1
        total_dropped_queues += trace.queues_dropped
        for name, ms in trace.stage_ms.items():
            per_stage.setdefault(name, []).append(ms)

    stage_p95 = {name: percentile(vals, 95) for name, vals in per_stage.items()}
    stage_mean = {name: statistics.fmean(vals) for name, vals in per_stage.items()}

    return {
        "trials": trials,
        "end_to_end_mean_ms": statistics.fmean(totals),
        "end_to_end_p50_ms": percentile(totals, 50),
        "end_to_end_p95_ms": percentile(totals, 95),
        "end_to_end_p99_ms": percentile(totals, 99),
        "naive_sum_of_stage_p95_ms": sum(stage_p95.values()),
        "naive_sum_of_stage_mean_ms": sum(stage_mean.values()),
        "stage_p95_ms": stage_p95,
        "stage_mean_ms": stage_mean,
        "cache_hit_rate_observed": cache_hits / trials if trials else 0.0,
        "avg_queues_dropped_per_request": total_dropped_queues / trials if trials else 0.0,
    }


def print_report(label: str, result: dict) -> None:
    print(f"\n=== {label} ({result['trials']} trials) ===")
    print(f"  end-to-end mean : {result['end_to_end_mean_ms']:7.2f} ms")
    print(f"  end-to-end p50  : {result['end_to_end_p50_ms']:7.2f} ms")
    print(f"  end-to-end p95  : {result['end_to_end_p95_ms']:7.2f} ms   <- what the request actually experiences")
    print(f"  end-to-end p99  : {result['end_to_end_p99_ms']:7.2f} ms")
    print(f"  naive sum of per-stage means : {result['naive_sum_of_stage_mean_ms']:7.2f} ms  (means always add exactly)")
    print(f"  naive sum of per-stage p95s  : {result['naive_sum_of_stage_p95_ms']:7.2f} ms  (this is the mistake)")
    gap = result["naive_sum_of_stage_p95_ms"] - result["end_to_end_p95_ms"]
    pct = gap / result["end_to_end_p95_ms"] * 100 if result["end_to_end_p95_ms"] else 0.0
    print(f"  naive estimate overshoots measured end-to-end p95 by {gap:7.2f} ms ({pct:.0f}%)")
    if result["avg_queues_dropped_per_request"] > 0:
        print(f"  avg recall queues dropped to timeout per request: {result['avg_queues_dropped_per_request']:.3f}")
    if result["cache_hit_rate_observed"] > 0:
        print(f"  cache hit rate observed: {result['cache_hit_rate_observed']:.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trials", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--recall-mode", choices=["serial", "parallel"], default="parallel")
    parser.add_argument("--recall-timeout-ms", type=float, default=None)
    parser.add_argument("--recall-candidates", type=int, default=3000)
    parser.add_argument("--prerank-candidates", type=int, default=300)
    parser.add_argument("--finerank-candidates", type=int, default=50)
    parser.add_argument("--cache-hit-rate", type=float, default=0.0)
    parser.add_argument(
        "--compare-serial-parallel", action="store_true",
        help="also run the identical config with the other recall mode, for a direct comparison",
    )
    parser.add_argument(
        "--compare-cache", type=float, default=None, metavar="HIT_RATE",
        help="also run the identical config with this cache hit rate, to compare mean vs p95 effect",
    )
    args = parser.parse_args()

    base_cfg = FunnelConfig(
        recall_mode=args.recall_mode,
        recall_timeout_ms=args.recall_timeout_ms,
        recall_candidates=args.recall_candidates,
        prerank_candidates=args.prerank_candidates,
        finerank_candidates=args.finerank_candidates,
        cache_hit_rate=args.cache_hit_rate,
    )
    print_report(f"recall={args.recall_mode} timeout={args.recall_timeout_ms} cache={args.cache_hit_rate}", run_harness(base_cfg, args.trials, args.seed))

    if args.compare_serial_parallel:
        other_mode = "serial" if args.recall_mode == "parallel" else "parallel"
        other_cfg = FunnelConfig(**{**base_cfg.__dict__, "recall_mode": other_mode})
        print_report(f"recall={other_mode} (same config otherwise)", run_harness(other_cfg, args.trials, args.seed))

    if args.compare_cache is not None:
        cached_cfg = FunnelConfig(**{**base_cfg.__dict__, "cache_hit_rate": args.compare_cache})
        print_report(f"cache_hit_rate={args.compare_cache} (same config otherwise)", run_harness(cached_cfg, args.trials, args.seed))


if __name__ == "__main__":
    main()
