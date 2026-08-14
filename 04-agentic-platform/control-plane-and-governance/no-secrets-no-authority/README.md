---
status: draft
level: reference
label: No secrets, no authority
---

# NVIDIA's six invariants, made concrete

> Dated survey, 2026-08-14. Source:
> [Secure Agent Workspace reference](https://docs.nvidia.com/enterprise-reference-architectures/secure-agent-workspace-reference-design/latest/reference-architecture.html).

**Question:** a governed agent needs invariants, not advice. NVIDIA's
reference architecture names six — and each one maps to a concrete
mechanism. What are they, and what does each defend against?

## The six invariants

**No raw provider credentials reach the agent** — a credential proxy
rewrites Authorization headers at egress; the agent receives capabilities,
not secrets. Defends against credential exfiltration.

**No self-granted authority** — the agent operates with a policy-defined
subset of permissions and cannot widen its own scope; widening requires a
re-issued signed delegation. Defends against privilege escalation.

**No connection to an unlisted destination** — deny-by-default at two
layers (workspace network boundary and runtime egress); adding a
destination is a control-plane change. Defends against exfiltration.

**No tampering with system binaries** — read-only filesystem outside the
writable agent home. Defends against persistence.

**No agent-created persistence** — shell startup files and agent config
are deny-write; they change only through control-plane operator action.
Defends against every-session persistence.

**No suppressed audit** — telemetry is emitted from trust-boundary
endpoints outside the agent's reach; the agent cannot disable it.
Defends against invisible escapes.

## Why invariants beat policies

Policies are instructions; invariants are enforceable properties. The
mission's guardrail is the same idea at mechanism scale: a patch touching
a test file is a failure *by construction*, not by request.

## What this does not say

It does not claim NVIDIA's reference is the only correct shape. It
presents the invariants as the audit checklist the stage argues every
control plane needs.
