---
status: draft
level: frontier
base: none
label: Context and memory
---

# Every session starts from zero. What does the agent carry in?

**Question:** [stage 06](../closing-the-loop/) showed the smallest form of
memory: feed a model the real outcome of its own failed attempt, and the
next attempt changes. But every new session starts from zero — the model
has no idea what the previous session learned, and a repository's
conventions are not in its weights. Production agents solve this with
three memory layers. What does each one hold, what does each one forget,
and how do you know which layer a failure came from?

**The artifact this stage follows** is [a-sqlite-memory](a-sqlite-memory/),
a real store seeded with six lessons this mission actually measured
([record](a-sqlite-memory/runs/2026-08-14-sqlite-memory.json)). Two
questions are asked against it, and the promotion that follows the second
recall is the stage's spine: every production memory stack below is that
store, at scale.

**Before this:** stage 06's one-loop feedback. This stage scales the loop
across sessions and codebases.

## The three layers, and what each one forgets

Memory is not one thing. It is three layers with different lifetimes and
different failure modes ([file-based-memory](file-based-memory/),
[memory-tiers](memory-tiers/)):

| Layer | What it holds | What it forgets |
|---|---|---|
| Instruction | the repository's static rules — AGENTS.md / CLAUDE.md, read at every session start | nothing silently, but everything when unpruned: an instruction file that never shrinks becomes noise |
| Generated | what the agent itself learned — session summaries the agent wrote | freshness: a summary can be stale, and it can drift from what the session actually established |
| Retrieval | knowledge that never fits the context window — RAG, codebase indexes | coverage: retrieval misses, and a miss is silent — the agent does not know it does not know |

The first layer is static and survives every session by design. Codex
separates AGENTS.md from auto-generated Memories; Claude Code reads four
CLAUDE.md scopes at session start and auto-captures learnings. The third
layer exists because the second one has a hard ceiling: a summary cannot
carry a whole repository, and a repository too large for the context
window needs a way to be *asked* rather than carried.

## The mechanism: promotion follows use, not sentiment

The demo's finding is the mechanism. The store holds six lessons, each
seeded from a real `runs/` record — haiku's 0/6 blind-call resolve, the
guardrail that fires only on the diff, the 18/18 harness resolve, the
0/12-to-2/12 feedback result. Two questions are recalled against them:

```text
question 1: "which tier should resolve it; what does the blind-call say?"
  recalled: lessons 1, 3, 4          -> promoted: none
question 2: "is the resolve rate still believable when nothing failed?"
  recalled: lessons 1, 4              -> promoted: 1 and 4 durable
```

Lesson 1 is recalled by both questions and becomes durable. Lesson 2 — the
guardrail claim — is recalled by neither, because neither question mentions
guardrails. That is the point: **the store does not decide what matters,
recall does**. A fact that is never recalled stays ephemeral, and an
unpruned instruction file is exactly a store where everything is durable
because nothing is ever filtered.

## The bottleneck is recall, not storage

The same demo shows where production memory actually spends its complexity.
`LIKE` keyword matching is visibly too weak for an open-ended question —
"is the resolve rate still believable" only matched lessons whose keywords
happened to co-occur. Storage was never the hard part; getting the right
fact in front of the agent at the right moment is. That is why the industry
layers above this store exist: Mem0's paper reports selective fact-based
memory cutting token cost by over 90% versus full-history prompting, and
Zep's temporal graphs track how facts change over time. Both are recall
engines, not storage engines.

## Retrieval: when RAG belongs in the loop, and when it does not

The third layer has its own decision rule
([when-rag-belongs-in-an-agent](when-rag-belongs-in-an-agent/),
[from-rag-to-agentic-rag](from-rag-to-agentic-rag/)). RAG belongs in an
agent when the task is open-world — the answer is not in context and not in
weights, and a retrieval *tool* the agent calls mid-task beats retrieval
pasted into the prompt. It does not belong when the fact is small, stable,
and known — that is what the instruction layer is for. The distinction
matters because a retrieval miss is silent: an agent that searched and
found nothing cannot tell "nothing exists" from "I searched wrong."

The same reasoning applies to codebases
([codebase-retrieval](codebase-retrieval/)): repo maps, symbol indexes, and
code-intelligence graphs exist because "monorepo blind spots" — searches
limited to the current directory — are the dominant failure in large-
project agent work. And a newer shape, filesystem-backed state
([agentfs-and-persistent-workspace](agentfs-and-persistent-workspace/)),
exposes agent memory as files, so the agent's most reliable capability —
file I/O — reaches state that otherwise needs a proprietary API.

## What this stage does and does not establish

It establishes the mechanism: three layers with distinct lifetimes, the
promotion-follows-use rule, and the recall-not-storage bottleneck, anchored
to the mission's own measured facts. The mechanism is verified by the
recorded store; the production claims are dated surveys with sources cited.

It does not claim memory improves resolve rate. The mission's own
closing-the-loop stage measured that question in its smallest form (0/12
to 2/12), and scaling it across sessions is a survey claim, not a number
this stage produces. It also does not claim the three layers are enough —
the point of naming each layer's forgetting is that every failure is
diagnosable: stale instruction, stale summary, or silent miss.

**Next:** the agent remembers. The next thing it needs is a way to agree
with the outside world on what a tool call means —
[tools and protocols](../tools-and-protocols/).
