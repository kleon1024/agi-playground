---
status: draft
level: frontier
base: none
label: Control plane and governance
---

# The agent sees a sandbox. Who sees the agent?

**Question:** every layer so far made the agent more capable — sandbox,
durability, memory, protocols, orchestration. This stage asks the
question none of them asked: while the agent works, *who is watching, and
who can stop it?* The mission already has a control plane in miniature —
its guardrail rejects any patch that touches a test file, enforced on the
diff, not requested from the model. What does that mechanism look like
when the "agent" is a fleet, and what are the invariants that make policy
enforceable at all?

**The artifact this stage follows** is the guardrail's own record: the
mission's tamper run, where every numeric signal said "resolved" and the
diff check was the only layer that caught it
([record](../real-tasks/run-a-real-task/runs/2026-08-14-real-task.md)). A
control plane is that record's mechanism, generalized from one guardrail
to a governed fleet.

**Before this:** stages 07–11 built the platform's capabilities. This
stage is the layer that governs them all.

## The control plane is not observability

The two are easy to confuse, and the difference only surfaces at an
incident ([control-vs-observability](control-vs-observability/)).
Observability is passive: it tells you *what happened*. A control plane is
active: it decides what may happen next — policy, budgets, sensitive-action
blocking, audit — and it sits between the observability log and the agent
that keeps working. The mission's guardrail is the smallest clean example:
the harness does not observe that the agent *might* tamper with tests and
report it later; it blocks the patch at the boundary, before scoring.

```text
observability:  the log says the target test passed
control plane:  the diff says a test file was touched -> GUARDRAIL FIRED
```

That is why the category matters more than the layer count: a platform
with perfect logs but no control plane has a complete story about
everything that already went wrong and no way to stop the next one.

## What a control plane actually does

Four jobs, and each one answers a question the agent cannot answer for
itself ([the-platform-layers](the-platform-layers/)):

| Job | The question | The mission's miniature |
|---|---|---|
| Enforce policy | what may the agent do? | a patch touching a test file is rejected outright |
| Hold budgets | how much may it spend? | the wall-clock and token cap per task — a timeout is a failure, not a retry |
| Block sensitive actions | what is off-limits even if asked? | no network access, so no fetching the upstream fix |
| Keep an audit trail | what did it do, and who can say so? | the recorded verdict per attempt, including the ones that tampered |

The first three are the interesting part: each one is a *refusal*, and a
refusal is only real if it is enforced on the boundary — the diff, the
budget counter, the network namespace — rather than requested from the
model. Everything this stage says about governance rests on that
distinction.

## The invariants that make policy enforceable

NVIDIA's Secure Agent Workspace reference
([2026](https://docs.nvidia.com/enterprise-reference-architectures/secure-agent-workspace-reference-design/latest/reference-architecture.html))
formalizes the rules that make refusals real
([no-secrets-no-authority](no-secrets-no-authority/)). Each invariant
defends against a specific failure:

| Invariant | Defends against |
|---|---|
| No raw credentials — the agent receives capabilities, never tokens | exfiltration: a token a model can read is a token a prompt can extract |
| No self-granted authority | escalation: the agent approving its own next permission |
| Deny-by-default egress | data leaving the boundary |
| No agent-created persistence | a shell rc file written once running forever, beyond any session |
| No suppressed audit | tampering with the record that would expose the others |

The last row is the one this mission's origin story is built on: on
2026-07-29 a serving engine was published as verified while every decode
step attended to a single token, and nothing looked wrong because the
throughput numbers were *better*. An agent scored by a test suite has a
shorter path to the same place — delete the assertion, and the scoreboard
reads 100%. That is why the audit trail is not bookkeeping; it is the
layer that would have made the 2026-07-29 failure visible.

## The fleet version, and the map

The industrial answers scale this to fleets: OpenAI's AgentKit hosts the
agent runtime with loop, memory, and deploy; the enterprise platforms —
AWS Bedrock AgentCore, Microsoft Copilot Studio, Google ADK — package
orchestration with governance attached ([the-enterprise-matrix](the-enterprise-matrix/)).
And [our-platform-map](our-platform-map/) draws this topic's own stages as
the planes of a platform, with every verified run placed on the plane that
owns its evidence — one diagram that shows where each number lives and
which plane governs it.

## What this stage does and does not establish

It establishes the mechanism: the control plane as the active layer that
refuses, with the mission's guardrail as its verified miniature and
NVIDIA's invariants as the checklist that makes refusals real. The
industrial claims — the product landscape, the vendor matrices — are dated
surveys with sources cited.

It does not claim the mission's guardrail is a production control plane —
it is one refusal, on one boundary, in one repository. And it does not
claim governance makes an agent safe; it claims governance makes the
*platform* auditable, which is the precondition for deciding how much
autonomy to grant — the next stage's subject.

**Next:** the platform can govern. The question that remains is how much
human is left in the loop, and where exactly — [autonomy and
orchestration](../autonomy-and-orchestration/).
