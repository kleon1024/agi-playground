---
status: draft
level: reference
label: Sandbox farms
---

# Provisioning isolation at scale: cold start is the throughput variable

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** one sandbox is easy; a fleet of thousands at agent scale is
an infrastructure product. What is the throughput variable, and where is
the break-even between managed and self-hosted?

## The throughput variable

Cold-start latency decides how many parallel agents a farm can support:
E2B runs Firecracker microVMs at ~150–200 ms from pre-warmed pools
([E2B](https://e2b.dev)); Northflank demonstrated 100,000 concurrent
sandboxes in 24 seconds from cold in its 2026 Scale Invitational
([Northflank](https://northflank.com/blog/ai-stack-for-enterprise-engineering)).
The pool size, not the VM, is the real capacity.

## Managed vs self-hosted

The break-even analysis (Spheron's 2026 setup guide) lands around 15
concurrent sandboxes: below that, managed (E2B) is cheaper after ops
overhead; above that, self-hosting Firecracker on bare metal wins on
density ([guide](https://www.spheron.network/blog/ai-agent-code-execution-sandbox-e2b-daytona-firecracker/)).
Sovereign or residency-constrained deployments push self-hosting earlier.

## Why this matters for this topic

The mission's local lane is the one-sandbox end of this curve; the
surveys document the fleet end. The execution-environment stage's demo
shows what a sandbox *does*; this chapter prices what a fleet *costs*.

## What this does not say

It does not claim a managed vendor is best — the break-even is
measured per deployment. It maps the variable and the trade.
