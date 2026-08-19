---
status: draft
level: frontier
base: none
label: Trust boundaries
---

# The agent reads untrusted text and runs untrusted tools. Where does trust actually sit?

**Question:** the execution stage built a sandbox and the governance stage
built a control plane. Both assume the boundary between the agent and the
world is a *place* — a filesystem scope, a network policy. This chapter
says the boundary is not a place but a property: the agent reads text it
does not control, and that text can tell it to do things. Prompt
injection, tool-output poisoning, and exfiltration are not sandbox
violations; they are failures of the trust boundary, which is a different
object.

**The artifact this chapter follows** is the failure taxonomy: every way an
attacker's text reaches the agent's actions, with the layer that must
defend each. The mission's guardrail is the smallest honest instance — it
defends one boundary against one attack.

**Before this:** [execution-environment](../../execution-environment/)
and [control-plane-and-governance](../../control-plane-and-governance/).
This chapter is the adversarial view of both.

## The boundary is a property, not a place

A sandbox answers "what can the process touch". It does not answer "what
can the *input* make the agent do". The difference is the whole threat
model of agentic systems:

| Attack | What happens | Why the sandbox does not stop it |
|---|---|---|
| Prompt injection | text the agent reads (a web page, an email, a tool result) instructs it to act | the act is performed by the agent inside its legitimate authority |
| Tool-output poisoning | a tool's result is crafted to look like success, steering the next action | the output is plausible; the sandbox sees a normal call |
| Secret exfiltration | the agent is prompted to include a credential in a tool call | the credential is inside the legitimate context |
| Capability confusion | an MCP server is trusted because it is connected, not because it is safe | MCP standardizes discovery, not trust |

Every row is the same shape: the *input* carries instructions the agent
cannot distinguish from its own task. The sandbox defends the process;
nothing in it defends the agent's judgment.

## The trust layers, from weakest to strongest

Production systems defend against these with layers, and the layers are
ordered by how much they trust the model:

| Layer | What it trusts | What it blocks |
|---|---|---|
| Prompt discipline | the model distinguishes instructions from data | little — a prompt is not a boundary |
| Input sanitization | the system can recognize hostile text | some — but the attacker controls the text |
| Tool contracts | the tool validates its own arguments | the specific abuse a contract checks |
| Capability minimization | the agent can only reach what the task needs | exfiltration and escalation |
| Independent verification | a verifier outside the agent checks the outcome | the whole class, if the verifier is strong |
| Human gate | a person reviews consequential actions | the rest |

The mission's guardrail sits at the strong end: it does not ask the model
to resist tampering, it checks the diff. That is the architectural lesson
generalized — the strongest trust boundary is the one that does not depend
on the agent being trustworthy. NVIDIA's invariant list
([stage 12](../../control-plane-and-governance/)) is the same principle
at fleet scale: no raw credentials, no self-granted authority,
no suppressed audit — each one moves the trust from the model to the
boundary.

## What the delivery stack adds

Three trust problems are specific to delivery and not to the harness:

**MCP provenance.** A tool registry is a trust surface: a malicious or
compromised MCP server is indistinguishable from a legitimate one to a
client that auto-connects. The delivery stack must treat every tool as
untrusted until it has provenance — who published it, what it declares,
what it can reach — which is the domain model's capability registry with
a trust column.

**Tenant isolation.** A delivery system that runs many agents must keep
their worlds apart — data, credentials, audit logs — even when the agents
share infrastructure. This is the execution stage's sandbox at the fleet
level, and it fails silently when a shared store leaks one tenant's state
into another's context.

**Audit integrity.** The control plane keeps an audit trail; a delivery
system's audit must be *append-only from the agent's perspective*, or a
compromised agent can erase the record of its own compromise. NVIDIA's
"no suppressed audit" invariant is the statement of this in one line.

## What the mission already proves

The mission demonstrates the strong-end mechanism at one-task scale: the
test-tampering guardrail catches a patch whose every other signal reads
as clean, because it verifies the diff from outside the agent. The
generalized claim — that independent verification is the strongest trust
layer — is supported by that recorded run, and the delivery-stack
extension is that the verifier must be outside the *system*, not just
outside the model.

## What this does not say

It does not claim prompt discipline is useless; it claims prompt
discipline is the weakest layer and cannot be the only one. It does not
claim a trust boundary makes the agent safe — it claims the boundary
makes the *failure* detectable, which is the difference the mission's
origin story depends on. And it does not claim the taxonomy is
exhaustive; it claims the rows name the attacks that recur, so a delivery
platform can audit which layers it actually has.

**Next:** boundaries have costs. The next object prices them —
[economics-of-autonomy](../economics-of-autonomy/).
