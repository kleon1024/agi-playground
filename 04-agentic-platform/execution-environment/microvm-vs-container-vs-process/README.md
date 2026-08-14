---
status: draft
level: reference
label: MicroVM vs container vs process
---

# Where the isolation boundary sits, and what it costs

> Dated survey, 2026-08-14. Cost and latency figures attributed to their
> sources; nothing measured here.

**Question:** the three-layer sandbox can sit at three different
boundaries — a subprocess, a container, or a microVM. Each trades
isolation strength against creation latency and density. Where does the
industry land, and why?

## The three boundaries

**Process** (the mission's demo): cheapest, fastest, weakest — the OS
shares the kernel, and any escape is a host escape. Good for mechanism
demos and low-risk work.

**Container** (gVisor, Kata): a second kernel or user-space boundary.
Stronger, still fast to start, still shares the host kernel unless Kata's
VM-based isolation is used.

**MicroVM** (Firecracker): a real VM boundary. E2B runs Firecracker
microVMs with ~150–200 ms create from pre-warmed pools and bills around
\$0.05/vCPU-hour
([E2B](https://e2b.dev); [Vercel/E2B comparison](https://vercel-docs.vercel.sh/kb/guide/vercel-sandbox-vs-e2b)).
The kernel is isolated per workload; an escape is still a host problem,
but the attack surface is dramatically smaller.

## Why microVMs won the agent-sandbox market

Agent sandboxes need two properties containers cannot deliver cleanly:
hard isolation for untrusted code, and fast creation for scale. Firecracker
was built at AWS for exactly this trade. Managed providers (E2B, Modal,
Northflank's 100k-concurrent-sandbox demonstrations) compete on the same
axis — cold-start latency as the throughput variable.

## The cost of the boundary

MicroVMs cost more per second and need pre-warmed pools to hit their
latency. The industry answer is a gradient, not a choice: process for
trusted local demos, containers for mid-trust work, microVMs for
untrusted cloud execution. The mission's local lane (a 24GB card) sits at
the process end by necessity; the surveys document the far end.

## What this does not say

It does not claim one boundary is always right — the threat model decides
(the `when-the-sandbox-leaks` chapter prices the failures). It maps the
three boundaries and their measured trade-offs.
