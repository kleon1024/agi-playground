# Production mapping

`core/orchestrator.py` builds one supervisor-and-workers scheduler: a task
graph with `reads`/`writes`/`depends_on`, a parallel-safety check, a
structured-return parser, and a token-cost tally. Nothing here claims that
scale is a limitation to graduate out of — the point, per the parent
[`README.md`](../README.md), is that the same five decisions this toy makes
explicit are the decisions every production multi-agent framework makes too,
usually without exposing them as directly. No benchmark numbers or success
rates are claimed anywhere on this page; this sub-lesson has no `runs/`
entry, and the only numbers that appear are the toy's own printed token
counts, reproducible by running `core/orchestrator.py`.

| Decision | This lesson (`core/`) | LangGraph | AutoGen / AG2 | CrewAI | Claude Code (published sub-agent design) |
|---|---|---|---|---|---|
| **Topology** | One fixed shape: supervisor dispatching to workers over a task graph. | A general graph of nodes and edges — any topology (pipeline, supervisor, cyclic) is expressible; this lesson's supervisor graph is one instance of it. | Conversation-centric: agents exchange messages in a group chat, with a selectable speaker-selection policy standing in for a supervisor. | Role-based crews with a configurable process (sequential or hierarchical), closer in spirit to this lesson's supervisor-and-workers split. | Runs multiple sub-agents concurrently per session in published 2026 write-ups, each spawned for a scoped piece of work rather than assembled into a persistent named topology. |
| **Parallel-safety rule** | Explicit and checked: `independent()` compares `reads`/`writes`/`depends_on` before two tasks may share a batch. | Left to the graph author — a node's edges express ordering, but nothing built in checks that two "parallel" branches do not share state. | Not applicable at the same granularity — a group chat is inherently sequential turn-taking, so the rule this lesson checks does not arise in the same form. | The hierarchical process manager decides task ordering; disjointness of outputs is a task-design responsibility, not a runtime check. | Sub-agent isolation is scoped by capability grant per session; disjointness of effects is an authorization-policy question, not an automatic graph check. |
| **Structured-return contract** | A minimal hand-parsed `STATUS:`/`ARTIFACT:` protocol; anything else raises `MalformedReturn`. | Node outputs are typed state updates against a schema (often a `TypedDict` or Pydantic model) merged into a shared state object — a stronger, framework-enforced version of the same idea. | Messages are free-form by default; structure is opt-in via function-calling-style tool schemas layered on top. | Task outputs can be typed via Pydantic models declared per task, enforced before a result is accepted downstream. | Structured, typed tool-call results throughout; a sub-agent's final report is expected to be actionable text the parent turns into further tool calls, not narrative prose. |
| **Context isolation** | Only a worker's parsed artifact — never its raw scratch reasoning — is what the supervisor accounts for as returned. | State passed between nodes is whatever the graph author includes in the shared schema; isolation is a design choice, not a default. | Each agent keeps its own conversation history; what crosses into the group chat is whatever that agent chooses to say, which can leak as much raw detail as the agent produces. | Each agent operates with its own context; crew-level context assembly is configurable per task. | Published write-ups describe each sub-agent starting from an isolated context with a narrow, task-scoped view — closest in spirit to this lesson's isolation claim. |
| **Cost accounting** | Every delegated task pays a fixed, explicit dispatch-and-return tax on top of its own work, tallied per run. | No built-in cost ledger; token accounting is left to whatever tracing/observability integration the deployment adds. | No built-in cost ledger; per-agent and per-message costs are visible only through external instrumentation. | No built-in cost ledger at the framework level. | Published write-ups mention cost and token accounting as an operational concern across concurrent sub-agents, without a specific formula disclosed. |
| **Debuggability** | One printed schedule, one result per task, one total — small enough to read end to end. | Graph execution can be traced node-by-node via the framework's built-in tracing integration. | Full message transcripts across all agents in the group chat, which grow with every additional participant. | Task and agent execution logs per crew run. | Full audit logging of every tool call — actor, action, arguments, result, risk tier — across every sub-agent, per the capability README's permission-ladder section. |

## Reading this table honestly

Five systems appear, not one, for the same single-vendor-rot reason the
capability [`LANDSCAPE.md`](../../LANDSCAPE.md) gives for single-agent
harnesses: LangGraph (graph-execution lineage), AutoGen/AG2 and CrewAI
(open-source multi-agent frameworks with different default topologies —
conversational versus role-based), and Claude Code's published sub-agent
write-ups (an industry deployment) span enough different design choices
that this lesson does not quietly anchor "what a multi-agent system is" to
one project's defaults. Every row above is a design decision, not a score.
The toy in `core/` makes each decision by hand, at a scale meant to be read
end to end; the frameworks in this table make the same decisions with far
more machinery, and disagree with each other about several of them —
which is itself evidence that none of these decisions has one obviously
correct answer yet.
