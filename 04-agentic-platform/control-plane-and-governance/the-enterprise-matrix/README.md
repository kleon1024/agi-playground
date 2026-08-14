---
status: draft
level: reference
label: The enterprise matrix
---

# Five vendor platforms, one table

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** every major vendor now sells an agentic platform. What are
the orchestration primitives, and how do the five platforms compare?

## The matrix

| Platform | Orchestration primitive | Runtime | Extensibility |
|---|---|---|---|
| AWS Bedrock AgentCore | Agent + Session + Workflow | GA since Oct 2025 | any framework/model |
| Microsoft Copilot Studio | Topic + Agent | Azure AI Foundry | Power Platform connectors + MCP |
| Google ADK + Vertex Agent Builder | Agent + Session + Workflow | Vertex | tool registry, A2A |
| OpenAI AgentKit | Agent + Thread | hosted agent runtime | Connector Registry, MCP |
| Anthropic (Claude Agent SDK + Managed Agents) | query/receive-response | sandboxed sessions | MCP |

Sources: [five-vendor framework matrix, 2026-05](https://agentmodeai.com/aws-microsoft-google-openai-anthropic-frameworks/);
[ISG buyers guide](https://research.isg-one.com/buyers-guide/artificial-intelligence/data-platforms/ai-agents/2026);
[A2A protocol coverage](https://agentmarketcap.ai/blog/2026/04/05/a2a-protocol-multi-framework-openagents-crewai-agent-interoperability).

## What the matrix shows

**Convergence on the same primitives** — agent, session, workflow, thread
— across all five. **MCP as the tool standard** — every platform speaks it.
**A2A as the interop layer** — agent-to-agent across frameworks.

## What this means for this topic

The topic's harness and demos are framework-agnostic by design — the five
decisions read the same on any of these platforms. The enterprise matrix
is the buy-vs-build surface the control-plane stage sits on.

## What this does not say

It does not rank the platforms — fit depends on existing stack. It maps
the primitive convergence that makes the five-decision reading portable.
