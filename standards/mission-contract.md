# The mission contract

A capability proves a hammer works. A mission proves a problem got solved.
That is a much stronger claim, so it needs a much stricter contract.

**No mission may be built before its `mission.yaml` is written.** Declaring the
baseline and the metric *after* seeing results is how you accidentally build a
system that optimizes whatever it happened to be good at.

## The file

Every `missions/<name>/mission.yaml`:

```yaml
stakeholder:      # who gets value — a person in a role, not "users"
job:              # what they are trying to accomplish
decision:         # the choice the system makes on their behalf
baseline:         # what they do today, and its measured cost
primary_metric:   # the one number that decides success
guardrails:       # what must not degrade, with thresholds
latency_budget:   # p50 and p95
cost_budget:      # per successful task, not per call
capabilities:     # which capabilities/ this composes
acceptance:       # conditions that must all hold
proves:           # what a passing run establishes
does_not_prove:   # what it does NOT establish — required
```

The last two fields are the ones that keep this honest, and they exist because
of a problem specific to a teaching repository.

## Outcomes cannot be run, so they must be proxied — explicitly

This repo's core invariant is that every published number traces to a `runs/`
entry: a command, hardware, wall-clock, and metrics. That works for technical
claims because they are reproducible.

Business outcomes are not. There are no real users here, no production traffic,
no retention curve. A mission that claimed "retention ↑ 12%" would be
fabricating, and one fabricated number costs more credibility than every
verified one earns.

So mission outcomes are proven against **reproducible proxies**, and each
mission must say which it used:

| Proxy | What it can support | What it cannot |
|---|---|---|
| **Offline replay** on a public logged dataset | Ranking/retrieval quality vs. a baseline on the same data | That live users behave like logged ones |
| **Simulated users** with a declared policy | Interaction dynamics, recovery, multi-turn behaviour | That real people share the simulator's preferences |
| **Public benchmark + stated baseline** | Capability comparison under a disclosed harness | Business value of the difference |
| **Cost and latency instrumentation** | Real budgets — these *are* directly measurable | Value delivered per unit cost |

Latency and cost are the exception: they are genuinely measurable here, and
missions must report them from real runs rather than estimates.

`does_not_prove` is mandatory and must be specific. "This does not prove
production retention improves; the replay set is 2023 logs and the user
simulator assumes stationary preferences" is acceptable. "Results may vary" is
not.

## Acceptance

A mission passes when **all** hold:

1. **It beats the declared baseline** on `primary_metric`, by a margin larger
   than the run-to-run variance — which means variance must be measured, not
   assumed. A single seed is not a result.
2. **It ran end to end**, live, as one system. Stage-by-stage success is not
   mission success; the integration is the thing being tested.
3. **No guardrail regressed** past its declared threshold.
4. **Latency and cost stayed inside budget**, measured on the real run.
5. **Failures are catalogued.** A mission report with no failure analysis has
   not been examined closely enough to be trusted.
6. **Everything is traceable**: metrics, cost, and failures each point at a
   `runs/` entry.

Failing a mission is a legitimate, publishable outcome. "We built it, and it did
not beat the baseline, and here is why" teaches more than a success with an
unstated baseline. What is not acceptable is quietly moving the metric.

## The capability admission gate

Capabilities are where scope dies. A capability enters the main curriculum only
if **all five** hold:

1. **Reused by at least two missions.** One mission needing it means it belongs
   *inside* that mission until a second one asks.
2. **Clear input/output contract**, so a mission can swap implementations.
3. **Objectively evaluable** on its own, independent of any mission.
4. **Has a toy → production mapping**: a readable implementation and the real
   system it mirrors.
5. **Runs on an existing compute lane**, or is explicitly labelled `scale-only`
   with the reason.

This is why `capabilities/` currently holds exactly one entry. Perception,
generation, ranking, and continual learning are named in the architecture
because the structure must have somewhere to put them — not because they are
half-built. An empty folder is a promise; this repo prefers to owe nothing.
