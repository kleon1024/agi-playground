---
status: draft
---

# 08 — Agents

**Goal:** build an agent harness from scratch — the loop, tool schemas,
context management, sandboxing, and sub-agent orchestration — and come out
able to read production harnesses (Claude Code, OpenHands, SWE-agent) as
elaborations on the same core loop, not as unrelated black boxes.

**Why this track is the flagship, not a bolt-on to a model demo.** The
research pass behind this repo's curriculum (see [`research/`](../../research/))
found agent harness engineering to be the least-served topic in the 2026
educational landscape, despite being — by the field's own recent literature —
the most industrially load-bearing one. A "harness" is the software layer
around the model that turns a next-token predictor into something that acts:
the loop that alternates reasoning and action, the schemas that let the model
call tools reliably, the logic deciding what context the model sees and when,
the sandboxing and permission boundaries around what it's allowed to do, and
the orchestration when one agent delegates to others. None of that is model
weights, and almost none of it is "just prompt engineering." A 2026 paper
title makes the stakes explicit — *"Stop Comparing LLM Agents Without
Disclosing the Harness"* — because two teams reporting different scores for
"the same model" on "the same benchmark" are, in practice, often just running
different harnesses. This track treats harness design as the subject, the
same way `06-inference` treats serving mechanics as the subject instead of
"go read vLLM."

## What you build

The seed lessons, `01-agent-loop-from-scratch` through
`04-sandboxed-execution`, are speedrun [stage 06](../../missions/01-language-model-agent/06-agent/): a
minimal harness at mini-swe-agent scale — the loop, 2–3 tools, context window
management, sandboxed execution — wrapping the model served by speedrun stage
05. `05-sub-agents-and-multi-agent` and `06-harness-aware-evaluation` are
track-only depth beyond what the speedrun needs: delegation patterns, and the
evaluation discipline that makes any harness-benchmark claim (including this
track's own) honest.

## What a harness actually is

Strip away specific frameworks and a harness is five decisions, made once and
then run in a loop: **(1)** how observation and action interleave — the loop
shape; **(2)** how the model requests an action and how the harness validates
and dispatches it — tool schemas; **(3)** what the model sees at each step and
how that's kept from growing without bound — context management; **(4)** what
the harness will actually let an action do, and under what confirmation — the
permission and sandboxing model; **(5)** whether and how one agent delegates
to another, and what each sub-agent does or doesn't see. Production write-ups
on Claude Code converge on a consistent 2026 lesson here: simplicity beats
complex orchestration, and permission/context-management design should be
settled *before* wiring up more model capability — a more capable model
running inside a badly designed harness underperforms a weaker model in a
well-designed one. This track builds each of the five decisions once, by
hand, in that order.

Run one grounded trajectory before reading the implementation patterns. Move
through the states and identify the exact boundary where the model must stop
generating and the harness must take control.

<!-- interactive: AgentLoopSimulator -->

## Conceptual spine

### The agent loop: ReAct and why interleaving beats either extreme

ReAct (Yao et al., 2022) interleaves **Thought → Action → Observation** steps:
the model reasons about what to do, takes an action, receives a real
observation, and reasons again with that observation in hand. This corrects
the failure mode of each pure alternative — chain-of-thought reasoning alone
has no way to check its claims against the world and can hallucinate facts it
never verifies; action-only agents with no interleaved reasoning can't adapt
when an action fails or returns something unexpected, because there's no step
where the model reconsiders. The loop's failure modes are specific and
recurring: repetition (retrying the same failed action because nothing in the
trace signals "this isn't working"), and — the more dangerous one for a
harness builder — **hallucinated observations**, where the model, mid-
generation, writes a plausible-looking "Observation:" itself instead of
waiting for the real tool result. The fix isn't a smarter model; it's a
harness discipline: hard-stop generation exactly at the observation boundary
and inject the *real* result, never let sampling continue past it. Getting
this one detail wrong silently breaks the loop's entire grounding guarantee.

### Tool schemas and function calling

Tools are defined as JSON Schema (name, description, parameter types,
required fields), and description quality matters as much as the name —
models rely on it to decide *when* and *how* to call a tool, not just that it
exists. Production models are fine-tuned on `(system-with-tool-defs, user,
assistant-with-tool-call)` triples so structured calling is a native output
mode rather than a prompted convention, which is why schema adherence is
generally reliable but not perfect: a harness needs a defined recovery path
for malformed calls (return the schema error as an observation, let the model
retry) rather than crashing on the first bad parse. `tool_choice` typically
comes in a few modes — `auto` (model decides whether to call anything),
`required` (must call some tool), a specific named function — and parallel
function calling (the model requests several independent tool calls in one
turn) is a real harness capability, not just a model trick: the harness has
to decide whether to dispatch them concurrently and how to reconcile
partial failures across the batch.

### MCP: standardizing tool integration, with the host as gatekeeper

Before MCP (Model Context Protocol), every harness wired up tool integrations
bespoke — a different adapter per model provider, per tool, per project. MCP
standardizes this into three primitives exposed by a **server**: **tools**
(callable functions, the direct analog of the schemas above), **resources**
(addressable read-only data the client can fetch without a full tool-call
round-trip, e.g. a file or a database row), and **prompts** (reusable prompt
templates the server offers, parameterized by the client). A **host**
application mediates between the model and any number of these servers,
which is the protocol's actual security contract: the host is the
gatekeeper deciding which servers a session may talk to and what a given
server is allowed to see or do, not the model and not the server itself.
This reframes tool integration as a distribution problem — write a server
once, and any MCP-compatible host can use it — rather than changing what a
tool call fundamentally is; the loop, schema-validation, and dispatch logic
this track builds in `02` apply whether the tool arrived via a bespoke
integration or an MCP server.

### Code-as-action and the agent-computer interface

Rather than one atomic tool call per operation, a **code agent** writes and
executes a snippet of code that can loop, branch, and chain several
operations in a single action — a general-purpose language composes better
than an enumerated tool menu once tasks require multi-step logic. The
underlying loop is generate → execute in a sandbox → observe stdout/stderr/
exception → on failure, feed the traceback back as context and regenerate
(**self-repair**). SWE-agent's **Agent-Computer Interface (ACI)** contributed
a specific, durable insight: tools *designed for* an agent measurably
outperform tools repurposed from human CLI conventions — an edit tool that
shows line numbers and rejects out-of-range edits catches errors a raw `sed`
invocation would silently corrupt. Sandboxing options for code execution
trade isolation strength against startup latency: a restricted subprocess is
cheap but weakly isolated; Docker/gVisor adds namespace and syscall
filtering at a few seconds of startup; Firecracker microVMs give
hardware-virtualization-level isolation at closer to VM cost, still fast
enough (~100ms class) to use per-task. The right choice depends on how
untrusted the code actually is, not on maximizing isolation by default.

### Agentic coding patterns, concretely

Production coding agents converge on a small number of recurring design
choices worth naming directly. **Cursor's two-phase edit** decouples
reasoning from precision: a large model proposes *what* to change in natural
language plus a rough sketch, and a small, specialized "Apply Model" turns
that intent into an exact diff against the real file — because "decide the
right change" and "place it exactly" are different skills with different
cost/reliability profiles. Comparing edit strategies (whole-file rewrite,
unified diff, search-replace blocks, line-range replacement), whole-file
rewrite counterintuitively scores highest on the Aider benchmark for many
models despite its token cost, because diff and patch formats are exactly
where models make small formatting mistakes that break the apply step —
precision of *intent* doesn't guarantee precision of *format*. **Explicit
planning** (a persistent plan or todo file the agent updates as it works)
outperforms purely implicit turn-by-turn proceeding on multi-step tasks,
because it survives context compaction: the plan is a checkable record
independent of whatever got summarized away.

### Multi-agent systems: coordination patterns and their real costs

Multi-agent orchestration comes in a few recurring shapes: **orchestrator-
worker** (a lead delegates to specialized sub-agents and integrates their
results), **peer group chat** (AutoGen-style — all agents see one shared
conversation, a speaker-selection strategy decides who talks next),
**declarative task graphs** (CrewAI — agents defined by role/goal/backstory,
tasks with explicit expected output and dependencies), **explicit state
graphs** (LangGraph — control flow as nodes and conditional edges, trading
"just prompt it" simplicity for auditable, resumable execution), and
**SOP-driven pipelines** (MetaGPT — a fixed sequence of role-specific
structured artifacts, e.g. PM writes a PRD → architect writes a design doc →
engineer writes code, rather than free-form chat). None of these patterns is
free. Multi-agent systems have three recurring failure modes: **coordination
overhead** (cost multiplies with agent count and round-trips), **error
compounding** (a wrong intermediate result gets treated as ground truth by
downstream agents with no way to independently verify it), and **context
fragmentation** (no single agent, and no single trace, holds the whole
picture, which makes integration failures unusually hard to debug). Multi-
agent orchestration earns its cost specifically when a task decomposes into
genuinely independent, separately verifiable sub-problems, or when a fresh,
uncontaminated context is itself valuable — an independent reviewer agent
catches things the original writer's context-anchored self-review reliably
misses, precisely because it never saw the writer's reasoning.

### Context management: eager loading, just-in-time retrieval, and compaction

**Eager loading** — stuffing everything potentially relevant into context
upfront — is simple and fine when the total fits comfortably, but wastes
budget and dilutes the model's attention once it doesn't. **Just-in-time
(JIT) loading** gives the agent tools to fetch only what it decides it needs,
when it needs it, and retrieval-augmented generation is the general case of
this pattern: dense-embedding retrieval (bi-encoder for recall) with
cross-encoder reranking for precision, often fused with sparse/BM25 search
via reciprocal rank fusion for hybrid search, chunked with a real trade-off
(too small loses surrounding context, too large dilutes the embedding's
specificity). Filesystem-native tools — grep, glob, direct file reads — are
the increasingly preferred JIT mechanism in coding-agent harnesses
specifically, because they're exact and debuggable versus embedding
similarity's approximate recall/precision trade-off; RAG earns its place
where content genuinely isn't addressable by exact search (large unstructured
corpora, semantic rather than lexical queries).

The eager/JIT split is a real, contested architectural choice among
production coding agents, not just a spectrum both ends of which are
equally valid in practice. Cursor's original design leans eager: it builds
and maintains an embedding-based index of the whole codebase upfront, so
retrieval at query time is a similarity search against a structure that
already exists. Claude Code leans JIT: no persistent index — the agent
issues grep/glob/read-file calls against the live filesystem on demand,
trading upfront indexing cost (and the staleness risk of an index that
drifts from the code as it changes) for exact, always-current results at
the cost of more tool round-trips per task. Neither is strictly better; the
index approach amortizes cost across many queries against a slow-changing
codebase, while the JIT approach never goes stale and needs no maintenance
step, which matters more in a codebase that changes turn by turn during the
same session the agent is working in.

As a session grows, **context compaction** keeps it bounded: naive
truncation (drop the oldest, cheapest, loses information irrecoverably), a
sliding window (same trade-off with a fixed size), or recursive summarization
(compress older turns into a running summary — preserves gist, loses detail,
costs an extra LLM call). MemGPT (Packer et al., 2023) frames this
explicitly as an OS problem: a tiered memory model — working "RAM" in the
active context, archival "disk" outside it — where the model itself calls
functions to page information in and out, rather than the harness silently
managing it behind the scenes. Production harnesses in 2026 (Claude Code's
practice is representative) mostly run the lighter-weight version of the
same idea: keep recent turns verbatim, summarize older turns once the
session approaches a context-budget threshold, without exposing MemGPT's
full explicit paging interface to the model. Stanford's Generative Agents
(Park et al., 2023) contribute a concrete, tunable retrieval formula worth
knowing regardless of which compaction strategy you build: weight candidate
memories by **recency** (exponential decay), **importance** (an
LLM-scored salience), and **relevance** (embedding similarity to the current
query) — turning "what should I recall right now" into a scored function
instead of a vague heuristic.

### Permission models, sandboxing, and prompt injection

**Capability-based permissions** — an agent holds only the specific, scoped
capabilities it needs for the current task (read this one directory, call
this one API with this argument shape) — fit an agent's ephemeral, per-task
nature better than identity-based ACL roles that grant standing broad access;
capabilities are naturally revocable, delegable, and auditable per action.
Risk-tiered confirmation is the practical policy: auto-approve read-only or
reversible actions, require human confirmation before destructive or
irreversible ones (delete, force-push, payment, send-email), hard-deny a
blocklist regardless of confirmation. The core design tension is that too
much confirmation friction gets rubber-stamped by a bored human — defeating
the entire purpose — while too little leaves real risk unmitigated; the fix
is making confirmation *rate* track actual risk, not raw action count. A
cheap, general-purpose way to lower that risk-per-action in the first place
— specifically for file-editing harnesses — is **git-as-undo**: commit (or
otherwise checkpoint) before letting the agent make a batch of changes, so a
bad edit is a `git revert` away rather than an unrecoverable mistake. This
doesn't replace risk-tiered confirmation (a destructive action against an
external system — a sent email, a production deploy — has no git to revert
it with), but for the common case of local file edits it turns "should I
confirm this?" into a lower-stakes question, because the cost of being
wrong just dropped.

Sandboxing tiers repeat the isolation/latency trade-off from code agents
above, applied to the whole harness's action surface. **Prompt injection** is
the harness-specific threat class: untrusted content the agent reads — a web
page, a file, a tool's returned data — can contain instructions that hijack
the agent's next action. **Indirect injection** (the malicious instruction
arrives via data being processed, not the user's own prompt) is the
dangerous case, because it breaks the harness's usual assumption that only
the user's own text needs scrutiny, and it is, honestly, not a solved
problem: AgentDojo (2024), a benchmark built specifically to measure this,
reported indirect prompt-injection attacks succeeding against a large
majority of the agent/defense combinations it tested at the time — a
2024-era figure against 2024-era defenses, not a current production number,
but the qualitative point has not been overturned since: no purely
prompt-level defense reliably closes this off. Defense is layered, not a
single fix: privilege separation (never let content read from an untrusted
source directly trigger a high-privilege action without a checkpoint),
treating any web/tool output as first-class untrusted data in prompt
construction rather than plain concatenated context, and audit logging
every tool call (actor, action, arguments, result, risk tier) — both for
forensics and because "we can reconstruct exactly what the agent did" is
itself a safety property.

### Sub-agents: isolation, depth limits, and why delegation actually helps

The harness-engineering angle on sub-agents is narrower than the coordination
patterns above: a sub-agent gets its **own clean context window** rather than
inheriting the parent's full history, and only its final result — not its
full transcript — returns to the parent. This isolation is what makes
delegation useful at all: a sub-agent researching one narrow question doesn't
drag the parent's unrelated conversation along, and its noisy intermediate
tool calls don't pollute the parent's context on return. The same
capability-based least-privilege principle from the permission model above
applies directly to delegation: a sub-agent should receive only the scoped
capabilities its specific delegated task needs (read this directory, call
this one tool), not a copy of the parent's full permission set — a
narrowly-scoped sub-agent is both safer and, in practice, more reliable,
because it can't wander into actions unrelated to the one thing it was
asked to do. Sub-agents spawning further sub-agents need a hard **depth
limit**, both for cost control (each level multiplies token spend) and
because coordination and error-compounding failure modes get worse, not
better, with more indirection. Modern harnesses run many sub-agents
concurrently — tens to hundreds per session in some 2026 write-ups — which
only works because each has an isolated context and a narrow, well-specified
task: this is an engineering property of the harness's concurrency and
result-aggregation logic, not a property of the underlying model.

### Harness design as the independent variable

Everything above compounds into the point this track closes on. *"Stop
Comparing LLM Agents Without Disclosing the Harness"* argues that published
agent-benchmark comparisons frequently differ more because of tool set,
context management, and retry logic than because of the model being swapped
— the harness accounts for more score variance than most papers disclose.
τ²-bench (Sierra Research, 2026) operationalizes a related point for
evaluation design specifically: it scores **dual-control** interactions
(both user and agent can call tools) on **policy adherence**, not just task
completion — did the agent follow the rules it was given while working, not
only whether the task got done. This is why `06-harness-aware-evaluation`
deliberately closes this track rather than treating evaluation as someone
else's problem: the loop, schemas, context strategy, and sub-agent design
built in lessons `01`–`05` are exactly what a fair harness comparison has to
disclose.

## Where harnesses actually fail, honestly

- **Context rot is real even inside the advertised window.** A model can
  technically fit a huge context and still perform worse than one given a
  carefully curated small one — irrelevant or stale content dilutes attention
  and raises the odds the model latches onto the wrong detail, independent of
  whether the tokens "fit."
- **Sub-agent results can silently contaminate the parent.** If a sub-agent's
  summary is wrong or overconfident, the parent has no independent way to
  check it — the isolation that makes delegation efficient is the same
  property that makes a bad sub-agent result invisible until it causes a
  downstream failure.
- **Unbounded sub-agent depth is a cost and reliability failure waiting to
  happen**, not just a theoretical risk — without a hard cap, a delegation
  chain can recurse far enough to make a single session unboundedly
  expensive before anyone notices.
- **A schema that worked yesterday can silently stop working** after a tool
  definition, a model version, or a prompt template changes — schema
  adherence is a probabilistic property of the model-plus-prompt, not a
  guarantee, and harnesses that don't validate and log malformed calls lose
  the signal that something drifted.

## Common misconceptions

1. **"More tools make a more capable agent."** Tool count adds selection
   complexity and failure surface (which tool, ambiguous overlaps) faster
   than it adds capability — a well-scoped 3-tool loop reliably beats a
   30-tool one on tasks within its scope, which is why mini-swe-agent's small
   toolset is a design choice, not a limitation.
2. **"A bigger context window solves context management."** Length and
   quality are different axes; a model that technically fits a huge context
   can still underperform one given a carefully curated smaller one, because
   irrelevant content dilutes attention rather than sitting inert.
3. **"Multi-agent systems are strictly more capable than single-agent
   ones."** Coordination overhead, error compounding across agent
   boundaries, and context fragmentation are real, recurring costs;
   multi-agent wins specifically when a task decomposes into independently
   verifiable sub-problems, not by default.
4. **"RAG and long context are competing solutions — pick one."** They
   compose: retrieval decides what's worth putting in context at all; long
   context decides how much you can afford once it's retrieved. A large
   window with no retrieval strategy is just eager loading at a bigger
   budget, not a fix for the underlying selection problem.
5. **"Prompt injection is a wording problem, fixable by telling the model to
   ignore instructions in retrieved content."** It's an architecture and
   privilege-separation problem — no system-prompt phrasing reliably stops a
   capable model from following instructions embedded in data it processes,
   so the real defense limits what a compromised turn can *do* (permission
   scoping, checkpoints before high-privilege actions), not how well the
   model refuses.

## Prerequisites

`06-inference` (this track needs a served model — your own or an API model —
to wrap in a harness) and `07-evals` (harness-disclosed evaluation
methodology applies directly to whatever harness you build here).

## Key papers and reference implementations

- Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*
  (2022) — the interleaved trace this track's `01` lesson implements from
  scratch.
- mini-swe-agent (the SWE-bench/SWE-agent team) — a real, working harness
  small enough to read in one sitting; this track's primary teach-from.
- Yang et al., *SWE-agent: Agent-Computer Interfaces* (2024) — tools designed
  for an agent, not repurposed human tools, as a measurable performance
  factor.
- Packer et al., *MemGPT: Towards LLMs as Operating Systems* (2023) — tiered
  memory as a function-calling interface the model itself drives.
- Park et al., *Generative Agents: Interactive Simulacra of Human Behavior*
  (2023) — the recency/importance/relevance memory retrieval formula.
- Published Claude Code system-design write-ups (2026) — production harness
  choices: simplicity over orchestration complexity, permission and
  context-management design preceding model integration.
- *Stop Comparing LLM Agents Without Disclosing the Harness* (2026) — the
  harness-as-independent-variable argument this track's closing lesson builds
  on.
- Sierra Research, τ²-bench (2026) — dual-control, policy-adherence
  evaluation, the template `06-harness-aware-evaluation` follows.
- Model Context Protocol specification — the tools/resources/prompts
  primitive split and host-as-gatekeeper security model this track's `02`
  lesson maps bespoke tool integration onto.
- Debenedetti et al., *AgentDojo* (2024) — the indirect-prompt-injection
  benchmark behind this track's "not a solved problem" framing in `04`; a
  2024-era measurement against 2024-era defenses, cited for its qualitative
  conclusion, not as a current attack-success rate.

## Hardware reality

Every lesson in this track runs against an API model or the model already
served by speedrun stage 05 — none of it needs local GPU compute beyond that
serving stage, so the local lane (or no GPU at all, for API-only work) is
sufficient for the whole track. `04-sandboxed-execution` needs real
container tooling (Docker at minimum) but no GPU. `05-sub-agents-and-multi-
agent` scales in dollar cost — API calls, not compute — worth tracking per
session the same disciplined way this repo tracks GPU dollar cost on Modal.

## Planned lessons

1. `01-agent-loop-from-scratch` — the ReAct-style observe-think-act loop, no
   framework, including the hallucinated-observation failure mode and its
   fix.
2. `02-tool-schemas-and-calling` — defining and dispatching 2–3 tools, schema
   validation, malformed-call recovery, parallel tool calls, and how MCP
   standardizes the same integration across hosts and servers.
3. `03-context-window-management` — eager vs. just-in-time loading,
   retrieval as one JIT mechanism, compaction and summarization strategies as
   the session grows.
4. `04-sandboxed-execution` — running tool actions (especially code
   execution) safely: sandbox tiers, capability-based permissions, risk-tiered
   confirmation, prompt-injection defense.
5. `05-sub-agents-and-multi-agent` — delegation with isolated contexts and
   depth limits; coordination patterns and their coordination-overhead,
   error-compounding, and context-fragmentation costs.
6. `06-harness-aware-evaluation` — evaluating the harness you built with the
   disclosure discipline from `07-evals`, using policy-adherence-style
   criteria alongside task completion.

## Next

This is the last numbered track. Speedrun [stage 06](../../missions/01-language-model-agent/06-agent/)
is where lessons `01`–`04` above integrate into the flagship path; from there,
[Track 07 — Evals](../../platform/evaluation-observability/)' harness-disclosed evaluation methodology —
already a prerequisite here — closes the loop these two tracks share: a
harness this track builds is only as credible as the eval that measured it.
