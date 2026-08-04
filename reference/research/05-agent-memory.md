---
level: reference
---

# Agent Memory Landscape (Mid-2026)

> Research pass conducted 2026-07-29; sources linked inline. Landscape facts
> reflect that date. This is a survey, not a run — no claim below is backed by
> a measurement in this repository, and the last section says what would be.

An agent's memory dies with its context window. Everything here is about what
people do next, and about one attribution that turned out to be false.

## (a) The "graph engineering" claim, and where it came from

In mid-July 2026 a framing spread quickly on X: prompt engineering gave way to
context engineering, then harness engineering, then loop engineering, and now
*graph engineering* — persistent knowledge graphs as agent memory, credited to
an unnamed senior Anthropic engineer and a leaked PDF.

[Turing Post traced the provenance](https://www.turingpost.com/p/is-graph-engineering-real-why-everyone-is-talking-about-it).
Peter Steinberger asked on X on 18 July 2026 whether the field had moved from
loops to graphs; hours later Hamel Husain published "Loop Engineering Is Dead.
Enter Graph Engineering." Neither works at Anthropic. Turing Post states
directly that **"Anthropic has not announced a discipline or product called
graph engineering."**

The claimed PDF does not survive comparison with itself:

| | [one viral post](https://x.com/0xCodez/status/2080250266851463209) | [another](https://x.com/zodchiii/status/2080738767594217589) |
|---|---|---|
| Length | 12 pages | 15 pages |
| Title | "Graph Engineering" | "Graph Engineering and Agent Memory" |
| Pipeline | Extract, Resolve, Assemble, Query, Repeat | Extract, Store, Retrieve, Evolve |

Same claimed artifact, different length, different title, different stage list,
no link to the document and no named author in either. The associated "18%
higher accuracy, 85% lower cost" figures trace, per the same analysis, to a
narrow academic paper on industrial diagrams, reframed as an industry-wide
result — Turing Post's summary is that "three different areas of work were
stitched together and presented as an industry-wide shift."

This belongs in a research directory rather than a footnote because it is the
same failure this repository legislates against elsewhere, moved one step back.
[The evidence standard](../standards/) says do not write a number you did not
measure. Its sibling: **do not write an attribution you did not locate.** A
claim's source is a claim.

## (b) What Anthropic has actually published on memory

Three things, none of them a graph.

**[Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)**
(2024) gives five composable orchestration patterns — prompt chaining, routing,
parallelization, orchestrator-workers, and evaluator-optimizer. This is the
material the "graph" framing describes, under plainer names and two years
earlier. None of it is new to software engineering either; state machines,
DAGs, and workflow engines have expressed the same structures for decades.

**[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)**
introduces the memory mechanism directly:

> "Structured note-taking, or agentic memory, is a technique where the agent
> regularly writes notes persisted to memory outside of the context window."

The named implementations are files — `NOTES.md`, `CLAUDE.md`, and a file-based
memory tool. The article also covers compaction (summarizing a conversation
near the context limit and reinitializing with the summary) and sub-agents that
return condensed results to a coordinator. It does not use the term "graph
engineering" and does not recommend knowledge graphs.

**The [memory tool](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool)**
is a client-side `/memory` directory with file create, read, update and delete,
available on Claude 4 and later. Storage is the developer's own infrastructure.

Two further moves in 2026 point the same way: on 2026-04-23 a memory-store
primitive shipped for Managed Agents — a workspace-scoped collection of text
documents the agent treats as a filesystem — and a dual-mode Classic versus
File Memory system distributing notes across topic-organized documents is
[reported in testing](https://www.testingcatalog.com/anthropic-plans-claude-memory-update-with-new-memory-files/).

**Every structural change in 2026 went further toward the filesystem.** The
direction of travel is the opposite of the one the viral framing asserts.

## (c) Storage shapes and what each costs

| Shape | Retrieval | Buys | Costs |
|---|---|---|---|
| One append-only file | read it all | nothing to build; nothing to go stale | grows past the context window, then unusable |
| File set plus an index | agent reads the index, opens what it needs | inspectable with the tools the agent already has; index is cheap to keep loaded | no ranking; relies on the agent choosing well |
| Fact table plus full-text and vector search | BM25 and embedding similarity | ranked recall over thousands of facts; recency and importance decay | no relations; every fact is an island |
| Typed property graph | multi-hop traversal from resolved entities | answers questions no single fact contains | an extraction step that fabricates relations and a resolution step that merges entities wrongly |

The last row is where the argument actually sits, and the decisive property is
not expressiveness — it is how each shape fails. A wrong file is wrong where
you can read it. A wrong edge makes traversal return the wrong neighbourhood
silently, and the answer that comes back is fluent either way. Two production
alternatives per row rather than one, per
[the landscape rule](../standards/): file-set memory is what Claude Code and
the Claude memory tool ship; graph memory is what the MCP knowledge-graph
memory server and Zep/Graphiti-style stores ship.

Note also that a file set with cross-references *is* a graph — filename as node,
link as edge, adjacency list stored as text. The interesting question is not
"graph or not" but **who materializes the edges, and what happens when they are
wrong.**

## (d) The measurement nobody publishes

Every writeup in this space describes a schema. None reports **edge density**:
relations per entity in a memory store that has been running against real
traffic for months.

That number decides whether any of it is real. A store with a triple table, a
BFS traversal function, and validity windows on every row is still a flat fact
list if extraction emits facts readily and predicates rarely — the traversal
starts from entities that have no neighbours and returns nothing, and the
retrieval quality you observe is entirely BM25's. The schema is not the graph.
The edges are the graph.

Two secondary numbers matter as much. **Attachment rate**: what fraction of
stored facts are linked to any entity at all, since an unattached fact is
unreachable by traversal by construction. And **supersession rate**: whether
anything with a `valid_until` column has ever had it set, because bitemporal
machinery that never fires is a schema comment, not a lifecycle.

This survey has none of these numbers for a store this repository can share.
A private store was inspected while writing it, and its figures are not
published here because they carry business context that is not ours to
distribute. Treat the paragraph above as a hypothesis with a known method, not
as a result.

## (e) What this means for the curriculum

Agent memory is **not admitted as a capability**. [The mission
contract](../standards/mission-contract.md) extracts a capability only after at
least two missions use the same input/output contract, and no mission here uses
persistent memory at all — mission 01's agent and mission 04's code agent both
start cold on every run.

[Mission 04](../../missions/04-code-agent/) is the natural first consumer, because
it already has the baseline the question needs: eighteen attempts across three
model tiers, every one starting from nothing, at \$0.16 to \$0.82 per resolved
task. "Does memory carried between attempts change resolve rate or cost per
resolved task?" is answerable against that with the scorer that already exists,
and it would produce the edge-density and attachment numbers section (d) is
missing.

Until a mission consumes it, agent memory stays here — a landscape note with an
open question attached, which is what this directory is for.

## Sources

- [Turing Post — Is Graph Engineering Real?](https://www.turingpost.com/p/is-graph-engineering-real-why-everyone-is-talking-about-it), provenance and the misattribution
- [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents), the five orchestration patterns
- [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), structured note-taking, compaction, sub-agents
- [Claude Docs — Memory tool](https://docs.claude.com/en/docs/agents-and-tools/tool-use/memory-tool), the file-based `/memory` interface
- [TestingCatalog — Memory Files](https://www.testingcatalog.com/anthropic-plans-claude-memory-update-with-new-memory-files/), the dual-mode system in testing; secondary source, unconfirmed
- The two X posts tabulated in section (a), cited as evidence of the claim's shape rather than as sources for any fact
