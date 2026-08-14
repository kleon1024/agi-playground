---
status: draft
level: reference
label: When the sandbox leaks
---

# The failure cases industry actually hits

> Dated survey, 2026-08-14. Sources cited inline.

**Question:** every sandbox has a bypass, and the industry has documented
the same few classes repeatedly. What are they, and which layer does each
one skip?

## The failure taxonomy

**Network bypass via the proxy.** A SOCKS5 proxy with a domain allowlist
is only as strong as its parsing: a domain that routes through a
permitted resolver, or a command that reaches the network without going
through the proxy, defeats the layer. Claude Code's own docs warn that
missing either the filesystem or network layer leaves a bypass
([sandboxing docs](https://code.claude.com/docs/en/sandboxing)).

**Allowlist gaps.** A domain allowlist with a wildcard, or a destination
the policy intended to block, is a hole. The fix is deny-by-default with
an explicit signed allowlist — NVIDIA's reference makes "no connection to
an unlisted destination" an invariant enforced at two layers
([Secure Agent Workspace](https://docs.nvidia.com/enterprise-reference-architectures/secure-agent-workspace-reference-design/latest/reference-architecture.html)).

**No network policy at all.** The simplest leak: an agent with a
filesystem sandbox but no network policy can exfiltrate anything it can
read. The three layers exist precisely because each is a separate class
of exploit.

**Agent-created persistence.** Shell startup files (`.bashrc`, hooks)
written once run on every future session, independent of the prompt.
NVIDIA's invariants make this explicit: "no agent-created persistence" is
enforced at the runtime sandbox, mutable only from the control plane.

**Invisible code strings.** The mission's own sandbox demo showed this:
paths inside `-c` code strings never appear in argv, so a static argv
check admits them. Production sandboxes close it with kernel-level
filesystem scope, which the demo cannot.

## What this does not say

It does not claim a perfect sandbox exists. It maps the documented failure
classes so a platform team can audit which layers their sandbox actually
enforces — the same audit the mission's demo performs at mechanism scale.
