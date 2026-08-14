---
status: draft
level: frontier
label: Agentic infrastructure
---

# Under the platform, what does the machine room look like?

**Question:** a control plane governs the fleet, but the fleet runs on
something: sandbox farms, model gateways, vector and memory stores,
observability pipelines, and the compute that serves inference. This layer
is the fastest-growing part of the enterprise AI stack, and every cloud
vendor now sells it as a named product. What actually sits in an agentic
infrastructure stack, and what breaks when it is under-provisioned?

**The artifact this stage follows** is the infrastructure map: the six
layers under a production agent — inference, sandbox execution, data and
memory stores, tool registries, observability, evaluation — drawn with the
mission's own compute reality (a 24GB local card) as the smallest honest
instance of each.

By the end you will be able to read any cloud's agentic offering (DigitalOcean's
AI-Native Cloud, AWS Bedrock AgentCore, Databricks memory positioning) as
the same six layers, and cost a deployment by its dominant constraint —
usually sandbox compute, not model tokens.

**Before this:** [stage 12](../control-plane-and-governance/) defined the
policy layer. This stage is the substrate under it; [stage 16](../industry-impact/)
asks what industries can actually stand the cost.

## What this stage decides

What to buy versus build, and where the budget goes. The industry
observation is that the agentic era inverts the cost model: orchestration
and sandbox compute become the dominant line, IDE seats shrink — and CI
speed becomes the throughput bottleneck on parallel agents.

## Planned chapters

- **[the-six-layers](the-six-layers/)** — inference (vLLM/SGLang serving), sandbox execution
  (E2B, Modal, Firecracker farms), data and memory stores (vector DBs,
  SQLite-first memory, Databricks/Snowflake repositioned as memory
  systems), tool registries and MCP servers, observability (OTel GenAI,
  Langfuse, LangSmith), evaluation — one map, six questions.
- **[sandbox-farms](sandbox-farms/)** — provisioning at scale: cold-start latency as the
  throughput variable (E2B 150–200 ms, microVM pools), self-hosted vs
  managed break-even, and the 100k-concurrent-sandbox scale claims.
- **[model-gateways](model-gateways/)** — routing, fallback, caching, and key management; the
  gateway as the layer where model choice becomes a config change, and the
  convergence with observability.
- **[the-compute-reality](the-compute-reality/)** — what a 24GB card can and cannot run; when to
  train locally and when the honest move is a dated external source — the
  same boundary the whole repository enforces.
- **[agentic-devops](agentic-devops/)** — running the machine room: rollout, canary, and
  incident response for agents that run unattended; observability-to-action
  loops (eval failure triggers a diagnosis run).

## Evidence strategy

All chapters are dated surveys of documented infrastructure; cost and
latency figures are attributed to their sources. No local runs are planned
— this stage is about reading the industry's machine room, and the
repository's own compute lane is already documented in `reference/`.

## Industrial grounding

Northflank's 2026 enterprise AI stack names agent runtime and sandbox
execution as one of the fastest-growing layers, with a 100k-concurrent
sandbox scale demonstration. DigitalOcean launched an AI-Native Cloud
integrating silicon-to-agents in five layers. Databricks and Snowflake are
repositioning as AI memory systems, and Cloudflare runs persistent agent
environments on Durable Objects. OpenAI's own stack moved orchestration and
sandbox compute to the dominant cost line, with CI speed as the parallel
agent bottleneck.
