---
status: verified
level: applied
verified: 2026-07-27
base: none
---

# Which stage do you cut to fit the request budget?

**Question:** the earlier stages could take as long as they needed. What changes when recall, pre-rank, fine-rank, the value tree, mixing, and rules must complete in one request under the mission's p95 300ms target? You need a measured latency budget, not a list of plausible stage times.

**Before this:** [stage 07's rule engine](../07-rule-engine/) — the last
stage in the funnel this budget has to fit, after recall, pre-rank, fine-rank,
the value tree, mixing, and rules have all run.

The artifact is an end-to-end distribution plus per-stage distributions. Mean is inadequate because a slow minority of requests is what users feel at the tail. The harness does not execute or time the funnel: it draws each stage's latency from a lognormal distribution whose median and spread are hand-chosen and disclosed in the script, then composes 5,000 such requests. That is a deliberate choice — the property this chapter teaches is how stage distributions compose, and a simulation isolates it from the noise of whatever else a developer machine is doing. With parallel recall and no cache, the sampled end-to-end mean was 31.22ms and p95 was 49.31ms. Read them as outputs of a declared model, not as timings of any real system.

## Do not add stage p95s

The central trap is treating end-to-end p95 as the sum of each stage's p95. A request is slow only when its own draws align in the tail; all stages' separate 95th-percentile requests usually occur on different traces. The parallel run's per-stage p95 sum was 54.74ms, 5.43ms above the sampled end-to-end p95. Means do add for the serial path; tail percentiles do not.

Recall demonstrates the other composition rule. Four queues run serially at the sum of their waits or concurrently at the slowest wait. In the same 5,000-trial run, serial recall produced 52.73ms mean and 72.71ms p95; parallel recall produced 31.22ms and 49.31ms. Parallel fan-out is not free, but it changes the request's critical path. A timeout should return a smaller union when a queue straggles rather than fail the whole request; that trades recall for tail latency and must be measured, not hidden.

<!-- interactive: LatencyBudget -->

There are two primary levers. Do less work: reduce the candidate count that expensive fine-rank scores after pre-rank has cut it. Do work concurrently: fan out independent recall queues. Stage 02's `prod/faiss_recall.py` is the concrete approximate-nearest-neighbour boundary; it trades exact recall for index latency rather than making exhaustive scoring appear cheap. A cache is a third, different tool. At an observed 0.803 hit rate, this run lowered mean to 7.00ms but p95 only to 34.52ms, because cache misses continue to populate the upper tail.

## Evidence boundary and production path

```bash
uv run python core/latency_pipeline.py --trials 5000 --compare-serial-parallel --compare-cache 0.8
uv run python prod/serving_harness.py --trials 1000
```

The core uses standard-library timing/distributions; its stage parameters are deliberately tuned and disclosed to show composition. The production harness uses NumPy and a thread-pool/async fan-out shape with a synthetic ANN catalogue. Alternatives include FAISS, ScaNN, or a managed vector service, paired with an HDR histogram or a metrics store that preserves tail samples.

This establishes the shape of latency composition in a declared per-stage latency model. Because the stage distributions are assumed rather than fitted to any real service, even the shape is only as good as those assumptions; what the run does establish is the composition arithmetic on top of them. It measures nothing about production hardware, real ANN recall, network queues, concurrent traffic, tail amplification from garbage collection, or a deployed service's p95. Therefore this stage cannot claim the mission is within its online budget.

## Next

[Stage 09 — the outcome report](../09-report/) consumes this stage's run
artifacts and refuses to declare mission success without end-to-end quality,
guardrail, cost, and failure evidence alongside it.

Trace IDs must join stage timing, timeout, cache status, candidate counts, and
the returned slate. Without that request-level record, a tail regression cannot
be assigned to the subsystem that owns it.

A useful production budget identifies an owner for each span and a measurement boundary: client-to-edge, gateway, retrieval fan-out, feature fetch, pre-rank, fine-rank, policy, serialization, and client rendering. Otherwise an apparent win can move time outside the dashboard rather than remove it. Trace IDs should join these spans for one request, while histograms summarize many requests. Percentiles should be calculated from the full population for the same route, hardware class, and experiment arm.

Timeouts need degradation semantics. If the lexical queue times out, record that it was absent and let the remaining queues compete; do not pretend the resulting slate had full recall. If fine-rank cannot return, a declared cheaper fallback can serve a reduced-quality slate, provided it preserves hard rules. The right decision depends on the user harm of waiting versus a weak recommendation. The required invariant is that a partial result is labelled in telemetry and evaluated as a separate slice.

Capacity planning is a separate question from a single-request histogram. At production load, queueing can dominate model execution and turn a healthy isolated p95 into an unhealthy service p95. Measure arrival rate, saturation, batch size, cancellation rate, and tail latency under representative concurrency. A model speedup may raise throughput but still worsen latency if it changes batching or contention. The core deliberately makes none of those claims; it establishes why the complete critical path, rather than a stage benchmark, owns the budget.

Cache correctness also matters. Personalised slates need a key that includes the user or cohort, relevant context, policy version, inventory freshness, and experiment arm. A broad cache key can create an impressive timing graph by serving the wrong page. A narrow one may produce little hit rate. The measured trade is therefore not “cache versus no cache,” but correctness-preserving hit rate versus the miss path that still determines tail experience.
