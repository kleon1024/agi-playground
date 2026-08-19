---
status: draft
level: frontier
base: none
label: Capstone A — software delivery
---

# A signal in, a merged change out. What does one complete delivery look like?

**Question:** the six objects are mapped. The question this capstone asks is
whether they can run as one system: a real signal in — a customer report, a
production alert, a vague feature request — and a merged, verified, landed
change out, with every handoff between the objects exercised. The mission's
[real-task run](../../real-tasks/) stopped at the guardrail; this capstone
names what the full chain is, which parts this repository can actually run,
and which part is the one that makes it a delivery rather than a fix.

**The artifact this chapter follows** is the delivery chain itself, drawn
as the nine handoffs with the object that owns each. This repository's own
site — a real deployed system with a test suite and a production surface —
is the running example the chain is anchored to.

**Before this:** the six delivery-stack objects and the verified core
([task set](../../task-set/) through [report](../../report/)). This
capstone composes them.

## Why the benchmark run is not a delivery

The real-task capstone ran a genuine bug through the platform and the
guardrail fired as designed. It was not a delivery, and naming why matters:

| A benchmark run | A delivery |
|---|---|
| task arrives with a test that defines done | a signal arrives with no done defined |
| the repository is the whole world | the world includes a deployed site, users, and SLOs |
| "done" is a passing test | done is a canary that holds its SLO |
| no approval, no deploy, no monitor | approval, deploy, and rollback are the point |
| the run ends when the test passes | the run ends when production agrees |

The last row is the sharpest. The mission's runs end at a green test. A
delivery ends at a *production outcome that survived observation* — which
is the [economics object](../economics-of-autonomy/)'s "time to external
outcome" made real.

## The chain, with its owner at each handoff

```text
signal          -> customer report / production alert / feature request
  | 1 ingestion -> normalize into a structured event (RunLedger)
  | 2 clarification -> resolve normative and authorization unknowns (ObjectiveSpec)
  | 3 ObjectiveSpec -> outcome, utility, constraints, owner (objective object)
  | 4 typed work graph -> tasks, dependencies, gates (WorkGraph)
  | 5 approval -> a human signs the graph and its gates (PolicyDecision)
  | 6 isolated implementation -> agent workers in sandboxes (harness)
  | 7 verification -> tests, security, integration (EvidenceRecord)
  | 8 PR + canary -> merged, deployed behind a gate (side-effect semantics)
  | 9 monitor -> SLO observation; accept or rollback (side-effect compensation)
  v
outcome         -> postmortem and improvement proposal (bounded-improvement)
```

Nine handoffs, and every one is owned by an object the previous six
chapters defined. The chain's value as a capstone is that it exposes which
handoffs the benchmark never exercised: 1 and 2 (signal and
clarification) are absent from a task set that arrives with a test; 5
(approval) is absent from a harness that pre-authorized everything; 8 and
9 (deploy and monitor) are absent from a repository with no production
surface.

## What this repository can run, honestly

This repository has exactly one real production surface: the site this
tutorial deploys to. A complete Capstone A would therefore be a real
signal about the site — a broken link report, a rendering defect, a
feature request for the docs — run through the chain to a merged change,
with the canary being the site build and the monitor being the deployed
page. That is the *target*; the honest status is that no such run has
been executed, and the chapter will not claim one. What the repository
already proves, run by run, is each segment in isolation:

- ingestion and clarification: the [intent stage](../../intent-to-plan/)
  and its ambiguity taxonomy;
- typed work graph: the [decomposer's lanes](../../intent-to-plan/decomposing-a-large-intent/);
- approval: the [authorization matrix](../../autonomy-and-orchestration/);
- isolated implementation: the [sandbox demo](../../execution-environment/);
- verification: the [scoring harness](../../verification-and-evals/) and
  the generality probe.

The missing segment is the one that makes it a delivery: canary deploy,
SLO observation, and rollback against the real site. It is missing because
it requires production authority, which is exactly what a tutorial on a
24GB laptop does not have — and naming that absence is part of the
capstone's honesty.

## The acceptance bar for a real Capstone A run

When a Capstone A run is executed, it must show, in one recorded chain:

1. a real signal about this site, with no test handed over;
2. an ObjectiveSpec that survived clarification — including a normative
   unknown the agent asked about instead of guessing;
3. a typed work graph approved by a human;
4. an isolated implementation whose diff passed tests *and* generality;
5. a canary that held or a rollback that fired, with the SLO recorded.

Items 1–4 are executable on the local lane. Item 5 is the production
gate that separates this capstone from the real-task run, and it is the
item the tutorial must not fake.

## What this does not say

It does not claim a delivery has been run — the chain is mapped, the
segments are proven, the whole is not. It does not claim the nine
handoffs are the only correct chain; it claims they are the minimal chain
that ends in a production outcome, which is the definition that separates
delivery from fix. And it does not claim the site is a production system
in the load-bearing sense — it is the one real surface this repository
has, and the difference between "real" and "load-bearing" is precisely
the gap the capstone names.

**Next:** the software capstone lands a change in production. The second
capstone lands a *finding* — the [science loop](../capstone-science-loop/).
