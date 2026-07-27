---
status: draft
---

# Agents: Landscape

Source: `research/synthesis.md` anchor table, "Agent harness" row.

| Toy (teach-from) | Production | Our take |
|---|---|---|
| mini-swe-agent (read in one sitting); build-your-own harness built in this track's lessons | SWE-agent (the Agent-Computer Interface framing), OpenHands, Claude Code (public write-ups on harness design), smolagents | mini-swe-agent is small enough to read completely and is a real, working harness — not a simplified stand-in. SWE-agent's ACI framing, OpenHands' broader tool ecosystem, Claude Code's published harness-design write-ups, and smolagents' lighter-weight framework approach give four distinct production reference points spanning research and industry lineages, so this track doesn't anchor to one harness's design choices. |

**Our take on harness design as the independent variable:** per the
synthesis's "harness disclosure matters" note, the loop design, tool schemas,
and context-management strategy taught in this track *are* the subject, not
implementation detail hidden behind a benchmark score. This is why
`06-harness-aware-evaluation` closes the track rather than treating
evaluation as someone else's problem.

**Single-vendor-rot note:** four independent production harnesses are named,
spanning academic (SWE-agent), open-source community (OpenHands, smolagents),
and industry (Claude Code) lineages.
