---
status: draft
level: reference
label: Model gateways
---

# Routing, fallback, caching: the layer where model choice becomes config

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the mission's routing decision (cheap vs frontier) is a
per-task policy. Infrastructure generalizes it: a gateway that routes,
falls back, caches, and manages keys so swapping models is a config
change. What does a gateway own, and where does it converge with
observability?

## What a gateway owns

**Routing** — per-request model selection (the FrugalGPT model-cascading
pattern the mission's tier routing implements at one task set's scale).

**Fallback** — provider outage handling.

**Caching** — semantic and prompt caching, the single largest token-cost
lever.

**Key management** — credentials held centrally, the credential-proxy
pattern from the governance stage.

The field: LiteLLM (self-hosted OSS), OpenRouter (managed), Portkey,
Vercel AI Gateway, Cloudflare AI Gateway
([gateway landscape](https://tokenjam.dev/blog/2026-05-26-the-9-layer-agent-ecosystem-map)).

## The convergence

Gateways and observability are the first pair to merge — a gateway already
sees every request and response, so adding measurement is a short step.
The mission's cheap-or-expensive stage is the gateway decision at
mechanism scale; the infrastructure version generalizes it across models
and teams.

## What this does not say

It does not claim a gateway replaces per-task policy — routing is the
enforcement point, but the policy (which task deserves which tier) stays
in the platform. It maps the layer and its convergence.
