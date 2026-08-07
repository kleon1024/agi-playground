---
status: draft
level: applied
label: Autonomous driving
---

# Can a policy that only imitated an expert in a simulator still drive in the loop?

**Question:** autonomous driving is the canonical example of learning
behavior from demonstration — a rule-based or human expert drives, and a
policy learns to imitate. But imitation accuracy on held-out examples is
not driving. A policy that perfectly reproduces the expert's decisions on
the training distribution can still steer off the road, because in the
loop its own mistakes compound into states the expert never visited.
Before asking whether a real autonomy stack is buildable, this topic asks
the question it can actually answer: does a small, from-scratch policy
trained only on expert demonstrations in a synthetic 2-D driving simulator
drive in the loop — and where exactly does it stop?

**The artifact this topic follows** is one closed-loop episode: a synthetic
road render in, a steering/throttle action out, and a run that either
reaches the target distance or ends in a collision or an off-road
excursion, recorded with the metrics that decide which it was.

## Why this topic exists

A real self-driving system is not buildable in this repository — no
vehicle, no sensor suite, no road network, and no way to verify a claim
about real-world driving. This topic exists because the method underneath
the marketing — imitation learning from expert demonstrations, evaluated
closed-loop — IS buildable at toy scale, and the discipline it requires is
the discipline every other topic here already applies: a declared baseline
written before the run, a closed-loop metric that cannot be gamed by a
model that merely matches training examples, and a stated boundary for
what the result does not prove.

The simulator is deliberately 2-D, synthetic, and CPU-cheap: a car on a
track with lane boundaries and moving obstacles, observed through a
low-resolution bird's-eye render. That is what makes the topic runnable in
seconds per stage — and the claim being tested is about the imitation-and-
closed-loop method, not about vision quality. If you came here for evidence
about real vehicles or real roads, it is not in this topic, on purpose.
Read [`mission.yaml`](mission.yaml)'s `does_not_prove` section before
treating any result here as more than that.

## What gets measured

The primary metric is **closed-loop episode completion rate** — the
fraction of episodes that reach the target distance without collision or
off-road excursion — reported beside **collision rate**, **off-road rate**,
and **training wall-clock**. No single number is reported alone: completion
rate without collision rate hides a policy that succeeds by ignoring
obstacles.

Three policies are compared on the same scenarios:

- **The rule baseline** — lane-following only, no avoidance logic. The
  floor a learned policy must clear.
- **The expert** — the same lane-following controller plus obstacle
  avoidance. The ceiling of what imitation can recover, since the learner's
  demonstrations come from it.
- **The cloned policy** — trained on expert demonstrations, evaluated in
  the loop.

The gap between held-out imitation accuracy and in-loop completion rate is
reported explicitly, because that gap is the finding: high imitation
accuracy with low completion rate is exactly the compounding-error failure
imitation learning is known for, and this topic measures it instead of
assuming it.

## Stages

| Stage | Question | Status |
|---|---|---|
| [00 — Scenario simulator](00-scenario-simulator/) | what makes a scoreable synthetic drive, generated rather than scraped? | verified |
| [01 — Perception baseline](01-perception-baseline/) | can lane offset and obstacle distance be recovered from the render, by hand and by learning? | verified |
| [02 — Expert policy](02-expert-policy/) | what does the rule-based expert actually achieve in the loop? | verified |
| [03 — Behavior cloning](03-behavior-cloning/) | does a policy trained on expert demos imitate well, and does that transfer to the loop? | verified |
| [04 — Closed-loop evaluation](04-closed-loop-eval/) | does the cloned policy clear the baseline, and where does it fall short of the expert? | verified |
| [05 — Harder scenarios](05-harder-scenarios/) | sharper curves and faster obstacles — does the boundary hold or break? | verified |
| [06 — Report](06-report/) | what did this prove, and what does it deliberately not prove? | verified |

## Model lineage

The method is a point on the imitation-learning line — ALVINN, DAVE-2,
DAgger, CARLA — and the closed-loop evaluation discipline is the same one
production autonomy stacks use. The
[open-source line behind autonomous driving](lineage.md)
traces it, including why closed-loop evaluation comes first.

## How to run

Every stage is CPU-only and runs in seconds:

```bash
cd 09-autonomous-driving/00-scenario-simulator/core
python generate_scenarios.py
```

Each stage's `runs/` entry records the exact command, hardware, wall-clock,
and metrics — the number you read in a stage README traces to that record,
never to an estimate.

