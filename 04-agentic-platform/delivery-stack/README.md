---
status: draft
level: frontier
base: none
label: Delivery stack
---

# Fixing a bug and delivering a result are different systems. What is the second one made of?

**Question:** every stage before this one built one thing: a harness that
turns a failing test into a passing patch, and measured the economics of
that loop. The [report](../report/) stage closed the loop on it honestly.
But *delivering* — a signal in, a validated outcome out, with state,
verification, and authority that survive across calls — needs more than a
harness loop. This stage is the map of what that second system is made of,
and it is honest about the gap: the first eighteen stages are the empirical
core; this one is the design agenda for what the core does not yet cover.

**The artifact this stage follows** is the object map: five core objects
that any autonomous delivery stack must carry, and two governance objects
that bind them. The mission's existing machinery maps onto the map — every
object below already has a partial instance in this repository — which is
how you can tell the map is not invented.

**Before this:** [stage 18](../report/) established what the harness
mission proves. This stage is what it does not yet prove, organized.

## Why the harness is not the delivery system

The mission's harness is excellent at what it owns: one task, a bounded
repository, a test that decides done. Delivery needs three properties the
harness never exercises:

- **State that outlives a run.** A delivery is many runs; the ledger of
  what happened, to what, and with what result must survive between them.
- **Verification that is not the executor.** The harness's test is
  separate from the model, but the delivery system's verification must be
  separate from the *system* — the layer that decides "done" cannot be a
  layer the delivery can rewrite.
- **Authority that is explicit.** Who may approve, what a budget is, what
  may be deployed — decisions the harness takes for granted (the
  maintainer pre-authorized everything) must be objects the delivery
  system can check.

A harness assumes all three; a delivery system must represent them.

## The five core objects

| Object | It answers | The mission's partial instance |
|---|---|---|
| **ObjectiveSpec** | what are we trying to achieve, under what constraints, and who decides? | [`mission.yaml`](../mission.yaml) — stakeholder, job, decision, metric, guardrails, budgets |
| **WorkGraph** | what work exists, and what depends on what? | the mined [task set](../task-set/) and the [decomposer's lanes](../intent-to-plan/decomposing-a-large-intent/) |
| **RunLedger** | what has been attempted, with what result? | the [recorded runs](../report/) — every verdict with its command and cost |
| **ArtifactGraph** | what was produced, and what does it depend on? | the diffs and generality probes of [stage 05](../cheap-or-expensive/) |
| **EvidenceRecord** | why is a verdict believed, and what does it not cover? | the [evidence contract](../verification-and-evals/) every run obeys |

Plus two governance objects: **PolicyDecision** (what may happen — the
[authorization matrix](../autonomy-and-orchestration/)) and
**ImprovementProposal** (what the system may change about itself — the
[closing-the-loop](../closing-the-loop/) finding, generalized).

## Why the map is not the system

The map's value is that each object is a *named gap*: this repository has
a partial instance of every one, and none is a complete delivery system.
`mission.yaml` is an ObjectiveSpec for a bug-fixing benchmark; a delivery
ObjectiveSpec must carry utility and trade-offs, not just constraints
([objective-and-decision-rights](objective-and-decision-rights/)). The
task set is a static WorkGraph; delivery needs one that evolves under
governance. The recorded runs are a RunLedger for two task sets; delivery
needs one that spans deployments.

Each sub-chapter takes one object and makes it concrete, in the same
tutorial shape as the rest of this topic: a real instance, a mechanism, a
boundary, and what the mission already proves about it.

- **[objective-and-decision-rights](objective-and-decision-rights/)** —
  what to achieve, how conflicts resolve, and who decides.
- **[domain-and-system-of-record](domain-and-system-of-record/)** — what
  the world contains, and which store is authoritative.
- **[side-effect-semantics](side-effect-semantics/)** — what "acted" means
  when the machine may act twice.
- **[trust-boundaries](trust-boundaries/)** — where trust sits when the
  agent reads text it does not control.
- **[economics-of-autonomy](economics-of-autonomy/)** — what a verified,
  landed outcome actually cost.
- **[bounded-improvement](bounded-improvement/)** — what the system may
  change about itself, and who controls the change.

**Next:** the first and least replaceable object — the objective, its
utility, and who owns the decisions —
[objective-and-decision-rights](objective-and-decision-rights/).
