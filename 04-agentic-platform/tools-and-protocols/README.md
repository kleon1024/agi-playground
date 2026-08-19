---
status: draft
level: frontier
base: none
label: Tools and protocols
---

# The harness calls a tool. What makes that call a contract?

**Question:** [stage 03](../agent-loop/) gave the harness three
hand-written tool schemas — `read_file`, `write_file`, `run_command` — all
owned inline by the same process. That works when the tool is yours. A
production agent calls tools across organizations: a search API, a
database, another team's service, another agent. An inline schema cannot
answer three questions the moment the tool is not yours: *what tools
exist? how do I call one? what does an error mean?* The answer became a
protocol. What does a protocol buy that a schema cannot?

**The artifact this stage follows** is [a-minimal-tool-protocol](a-minimal-tool-protocol/),
the smallest honest tool protocol on real task data
([transcript](a-minimal-tool-protocol/runs/2026-08-14-tool-protocol.md)):
discovery, two successful invocations, two structured errors. Every
production protocol below — MCP, an SDK's managed loop — is that
transcript, at scale.

**Before this:** stage 03 owned its tools inline. This stage externalizes
the contract.

## What an inline schema cannot answer

The stage 03 harness knows its tools because it wrote them. The moment the
tool lives elsewhere, three things break:

| Question | Inline schema | Protocol |
|---|---|---|
| What tools exist? | hard-coded in the harness | discovery is a first-class operation — the client asks |
| What does an error mean? | a string, if anything | structured codes — "bad parameter" is not "no such method" |
| What may not be called? | nothing stops the harness | the protocol is closed — a call outside it fails |

The third row is the one that matters for *accountability*, and the
distinction is worth being precise about. A raw function call has no
boundary: whatever is in the process can be invoked. A protocol's method
set is an enumerable surface — `delete_task` fails because it is not in
the protocol, so the attack surface is *listable*, which is the
precondition for auditing it. Enumerability is not safety: a protocol
that lists a dangerous tool, accepts poisoned tool output, or grants
excess permissions is still unsafe — the protocol just makes the unsafe
part inspectable. MCP standardizes discovery and invocation; it does not
supply tool trustworthiness, least privilege, or side-effect semantics,
which are the control-plane's job ([stage 12](../control-plane-and-governance/)).

## The contract, read

[a-minimal-tool-protocol](a-minimal-tool-protocol/) runs the three
operations on the mission's real task records:

```text
== discovery ==
{"tools": {"list_tasks": {...}, "get_task": {...}, "target_tests": {...}}}

== get_task ==
{"task_id": "private-b81c414", "subject": "fix(serve): attend past the
first token in every cached decode step"}

== error path ==
{"error": {"code": -32602, "message": "unknown task_id"}}
{"error": {"code": -32601, "message": "method not found: no_such_method"}}
{"error": {"code": -32601, "message": "method not found: delete_task"}}
```

The error codes are the contract. `-32602` says the *caller* was wrong —
the parameter is invalid. `-32601` says the *protocol* was wrong — the
method does not exist. A raw function call collapses both into "it
failed"; a protocol tells the agent which side to fix, which is exactly
what a loop needs to decide its next move.

## The evolution: from function calling to a standard

MCP took this floor and standardized it
([from-function-calling-to-mcp](from-function-calling-to-mcp/)): JSON-RPC
2.0 with three primitives — tools (callable), resources (readable), and
prompts (templates) — so that one server can be discovered by any client.
What the standard changes is the ecosystem: a tool written as an MCP
server is composable by every harness that speaks the protocol, instead of
reimplemented per integration. The production concerns that follow are
transport and auth ([mcp-in-production](mcp-in-production/)), and the
2026 reference split — the sandbox as the execution plane, MCP as the
tool-discovery layer, managed agents tunneling from headless sandboxes
into MCP servers — is the same three-layer logic as
[stage 07's execution environment](../execution-environment/), applied to
tools instead of processes.

## The other way to buy the contract: an SDK

There is a second production answer, and it inverts where the loop lives
([agent-sdk-composition](agent-sdk-composition/)). The OpenAI Agents SDK
ships the agent loop itself — Runner, guardrails, handoffs, subagents —
as a library you import instead of build. The tool contract is still
there; the SDK just owns the machinery around it. The decision is
ownership: a protocol externalizes the contract and lets you compose
anyone's tools, an SDK internalizes the loop and lets you ship faster at
the cost of being inside someone's harness. The mission's own choice —
importing a harness and adding tools to it — is the SDK path at a smaller
scale.

## What this stage does and does not establish

It establishes the mechanism: discover, invoke, error, result as the
contract shape, with structured errors that tell the loop which side to
fix, verified by the recorded transcript on real task data. The production
claims — MCP's ecosystem value, transport and auth behavior, SDK
guarantees — are dated surveys with sources cited.

It does not claim a protocol makes integration free: it makes integration
*auditable*, which is a different and smaller claim. And it does not claim
one answer is always right — the inline/protocol/SDK decision is an
ownership trade, and the mission sits on the inline end of it by design.

**Next:** one agent and its tools have agreed on a contract. The next
question is how a task that needs *twenty* agents and their contracts is
organized — [orchestration and workflows](../orchestration-and-workflows/).
