---
status: draft
level: frontier
label: Execution environment
---

# Where does the agent actually run, and what can that place do to it?

**Question:** stage 03's harness executed tools in a process on our
machine. Production agents run in sandboxes — process isolation, network
policy, and approval routing — because an agent that can read the whole
codebase needs a blast radius someone understands. What are the layers of
that isolation, and when is a container not enough?

**The artifact this stage follows** is the execution plane of the platform:
a minimal sandbox built by hand, plus a map of the industrial options
(process → container → microVM) with their measured creation time,
isolation, and cost.

By the end you will be able to read any production sandbox (Claude Code's,
Codex's, E2B's, a cloud agent's) as the same layers — filesystem policy,
network policy, approval policy — and say which layer a given exploit
bypasses.

**Before this:** [stage 03](../agent-loop/) ran tools unsandboxed. This
stage adds the isolation the industry puts around that loop, and it feeds
the platform map in [stage 12](../control-plane-and-governance/).

## What this stage decides

How much of the host the agent can see, reach, and change. The decision is
not "sandbox or not" — it is which of the three layers (filesystem,
network, approval) the harness enforces, because each missing layer is a
separate class of exploit.

## Planned chapters

- **[a-minimal-sandbox](a-minimal-sandbox/)** (local mechanism demo) — extend the stage 03
  harness with a subprocess sandbox: read-only filesystem outside a writable
  workdir, an allowlist-checked command gate, and a recorded run showing a
  deliberately destructive tool call being refused.
- **[the-sandbox-layers](the-sandbox-layers/)** — process isolation, network policy, approval
  routing as three independent layers; Claude Code's sandbox (SOCKS5 proxy,
  domain allowlist) and Codex's three-layer model read side by side.
- **[microvm-vs-container-vs-process](microvm-vs-container-vs-process/)** — E2B's Firecracker microVMs
  (150–200 ms create, ~\$0.05/vCPU-hour) vs gVisor/Kata vs a bare subprocess:
  what each buys and costs, and where the industry lands per threat model.
- **[fuse-and-the-filesystem-interface](fuse-and-the-filesystem-interface/)** — the filesystem as an agent
  interface: BranchFS copy-on-write branches for agentic exploration,
  AgentFS mapping agent state to a POSIX tree, and why a filesystem that
  snapshots and commits is a natural fit for an agent that must explore.
- **[when-the-sandbox-leaks](when-the-sandbox-leaks/)** — the failure cases industry actually hits:
  SOCKS5 bypass, allowlist gaps, missing network policy, agent-created
  persistence (shell rc files) — and the NVIDIA reference architecture's
  invariant list that exists precisely to close them.

## Evidence strategy

`a-minimal-sandbox` is a real local run with a recorded refusal in `runs/`.
The rest are dated surveys of documented products and the NVIDIA Secure
Agent Workspace reference architecture; creation-time and cost numbers are
attributed to their sources, not measured here.

## Industrial grounding

Claude Code v2.1.0+ enforces filesystem scope and routes all sandboxed
network traffic through a SOCKS5 proxy with a domain allowlist. Codex
documents process isolation, network policy, and approval routing. E2B runs
Firecracker microVMs at 150–200 ms create. NVIDIA's Secure Agent Workspace
reference (2026) enumerates six architectural invariants — no raw
credentials, no self-granted authority, deny-by-default, no agent-created
persistence, no agent-controlled lifecycle, no suppressed audit.
