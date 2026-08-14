---
status: draft
level: reference
label: The sandbox layers
---

# Process isolation, network policy, approval routing

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** the stage's demo showed three policy layers in 200 lines.
The production versions enforce the same three layers at the kernel,
proxy, and policy boundaries. What exactly does each layer block, and
what does an exploit that bypasses one still face?

## The three layers, in production

**Process isolation** — what the agent's code can do to the machine:
read-only filesystem outside the workspace, no access to system binaries
or shell startup files. Claude Code's native sandbox (v2.1.0+) enforces
filesystem scope directly
([docs](https://code.claude.com/docs/en/sandboxing)); Codex's sandbox adds
the same boundary with `sandbox_mode` from `read-only` to
`workspace-write`
([docs](https://developers.openai.com/codex/concepts/sandboxing)).

**Network policy** — where the agent can reach: Claude Code routes all
sandboxed traffic through a SOCKS5 proxy with a domain allowlist; Codex
denies by default and allows only listed destinations. An agent that can
read the codebase but not exfiltrate it has a bounded blast radius.

**Approval routing** — what the agent may do without asking: Codex's
`approval_policy` (untrusted / on-request / never) and Claude Code's
permission ladder are the third layer, and they exist precisely because
isolation cannot tell a legitimate destructive command from an escaping
one.

## The independence property

The layers are independent: an exploit that skips one still crosses the
next. NVIDIA's Secure Agent Workspace reference
([2026](https://docs.nvidia.com/enterprise-reference-architectures/secure-agent-workspace-reference-design/latest/reference-architecture.html))
formalizes this as deny-by-default at two layers (workspace network
boundary and runtime-sandbox egress), and the mission's sandbox demo
showed the same property in miniature — the `-c` code-string escape
passed the filesystem layer but would still face the network layer.

## What this does not say

It does not claim any product enforces all three perfectly — sandbox
bypass write-ups are the stage's `when-the-sandbox-leaks` chapter. It
maps the layers every exploit must cross.
