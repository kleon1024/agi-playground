# Production mapping

`core/` builds a harness at mini-swe-agent scale: one loop, three tools, one
context-compaction policy, one permission ladder. Nothing here claims that
scale is a limitation to graduate out of — see "why more tools does not make
a better agent" in [`../README.md`](../README.md). This page maps each design
decision to how three real, actively maintained harnesses handle the same
decision at production scale, per the toy/production split in
[`capabilities/act-coordinate/LANDSCAPE.md`](../../../../capabilities/act-coordinate/LANDSCAPE.md).
No benchmark numbers or scores are claimed anywhere on this page — this is a
map of design decisions, not a performance comparison, and this stage has no
`runs/` entry to cite one from yet.

| Decision | This stage (`core/`) | mini-swe-agent | OpenHands | Claude Code (published write-ups) |
|---|---|---|---|---|
| **Loop** | One Python function, `run_agent`: observe → decide → act → observe, explicit `Final Answer` / `max_steps` stop conditions. | Same shape, small enough to read in one sitting — this stage's closest anchor. | Wraps the same interleaving in an event-stream / agent-controller abstraction so one loop implementation serves many agent types and sandboxed runtimes. | Public 2026 write-ups describe the same interleaving with much heavier engineering around *what surrounds* each step, not a different loop shape. |
| **Tools** | 3 hand-written Python functions with hand-rolled JSON-Schema-subset validation (`validate_arguments`). | A comparably small, hand-picked set — the design point this stage borrows directly. | A much larger built-in tool ecosystem, plus MCP server integration for arbitrary externally-defined tools. | Built-in tools plus MCP servers; tool definitions are still name/description/schema underneath, same as here. |
| **Tool-call format** | Textual `Action: <name>` / `Action Input: <json>`, parsed with a regex, because it works against any model — tool-calling fine-tuned or not. | Textual, for the same reason: model-agnostic by construction. | Structured function-calling where the underlying model supports it, textual fallback otherwise. | Structured tool-call fields as the default path — no free-text parsing step at all against a model with native tool-calling support. |
| **Grounding rule** | `enforce_grounding`: `stop=["Observation:"]` passed to the backend, plus an unconditional truncate-after-stop-token as defense in depth, before the response is ever parsed. | Same two-layer discipline — a stop sequence isn't trusted to be honored by every backend. | Same discipline, applied uniformly across whichever backend a given session is configured against. | Native tool-calling removes the *parsing* step (the model emits a structured call object, not prose to regex out of), but the underlying discipline is identical: never let sampling continue past where a real result belongs. |
| **Sandboxing `run_command`-equivalent** | Argv-allowlist (checked post-`shlex.split`, never `shell=True`), timeout, output truncation, `cwd`-jail via `resolve_in_jail`. | Comparable subprocess-level sandboxing at a similar scope. | Full container/VM-level isolation (Docker, and gVisor/Firecracker-class options) for code execution — the isolation-tier ladder from the capability README's sandboxing section, several rungs up from an allowlist. | Published write-ups describe layered sandboxing plus explicit privilege separation for anything touching an external system, well beyond a single-process jail. |
| **Context management** | `estimate_tokens` (chars/4) + `drop_oldest_tool_results`: collapse superseded file reads, then drop-oldest under a hard floor. | A comparably lightweight policy — no persistent index, no separate retrieval subsystem. | Configurable context strategies, including retrieval over larger histories. | Leans just-in-time by design per the capability README: no persistent codebase index, live `grep`/`glob`/file-read calls against the filesystem on demand, trading upfront indexing cost for results that never go stale. |
| **Permissions** | A 3-tier enum (`AUTO` / `CONFIRM` / `DENY`) per tool, enforced by `check_permission`, with a fail-closed default (`default_confirm` denies everything). | A comparably simple confirmation model at this scale. | Configurable, more granular per-action policy across a larger action surface. | Full audit logging of every tool call (actor, action, arguments, result, risk tier) plus capability-scoped sub-agent permissions, not just a per-tool tier. |
| **Sub-agents** | Not built at this stage — see track `05-sub-agents-and-multi-agent`. | Single-agent by design. | Supports delegation across specialized agents. | Runs many sub-agents concurrently per session in some 2026 write-ups, each with an isolated context and a narrow, scoped capability set. |

## Reading this table honestly

The point of naming four systems, not one, is the "single-vendor-rot" note
from the capability README's landscape file: mini-swe-agent (research
lineage), OpenHands and smolagents (open-source community), and Claude Code
(industry) give independent reference points spanning different lineages, so
this stage doesn't quietly anchor its idea of "what a harness is" to one
project's specific choices — a real risk given how fast individual tools in
this space get acquired, rebranded, or archived. Every row above is a design
decision, not a score: the loop, schemas, grounding rule, and permission
ladder built in `core/` are the same five decisions every harness in this
table makes, at a scale meant to be read in one sitting rather than adopted
wholesale.
