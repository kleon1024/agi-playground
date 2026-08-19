---
status: draft
level: frontier
base: none
label: Domain model and system of record
---

# The agent needs to know what the world is. Where does that knowledge live?

**Question:** an objective says what to achieve. Before the agent can act
on it, it has to know what the world contains: which entity a table
describes, which service owns a record, which customer must never be
auto-contacted, which experiment sample came from which batch. A general
model has none of this. The delivery stack's second object is the domain
model and the system of record — the answer to "what is the world, and
which store is authoritative for each part of it?"

**The artifact this chapter follows** is the mission's own domain model in
miniature: the task record ([stage 00](../../task-set/)) and the path jail
([stage 07](../../execution-environment/)). They answer "what is the world"
for one narrow world — a repository where a test decides done — and the
chapter generalizes from there.

**Before this:** [objective-and-decision-rights](../objective-and-decision-rights/).
An objective names what to achieve; this object names what exists.

## The question the harness never had to ask

The mission's harness works because its world is tiny and already
represented: the repository is the world, files are the entities, the test
suite is the verifier, and `source_files` / `target_tests` in the task
record name exactly which part of the world a task touches. No ambiguity —
the record *is* the system of record.

Delivery breaks that assumption in three ways, and each is a question the
agent must be able to answer before it acts:

| Question | Benchmark world | Delivery world |
|---|---|---|
| What exists? | the repository tree | entities across systems — customers, orders, services, samples |
| Which store is authoritative? | the working tree | one system of record per entity, and the agent must know which |
| Who owns it? | nobody — one repo | a domain team, a service owner, a legal owner |
| What may I touch? | the jail | capabilities granted per entity, not per tool |
| What must never change? | tests | contracts, PII, audit invariants |

A model that guesses these answers is not wrong in a recoverable way — it
acts on a belief about the world, and the belief can be wrong *silently*:
a table updated in the wrong database is a "successful" run with the wrong
result.

## What a domain model actually contains

Generalize the mission's implicit model and you get four parts
([Restato's ontology-as-operating-layer](https://restato.github.io/blog/ontology-operating-layer-for-ai-agents/) is a good articulation; the shape is
the same in every vertical platform):

1. **Entities** — the things the world holds, with their types and
   relationships. A customer has orders; an order has lines; a sample came
   from a batch.
2. **System of record** — for each entity, which store is authoritative
   and which copies are derived. This is the load-bearing part: an agent
   that writes the derived copy has "succeeded" at writing and changed
   nothing that matters.
3. **Dependency graph** — which entities depend on which, so a change
   knows its blast radius and its ordering.
4. **Capability registry** — what actions are possible against each
   entity, and who is authorized to perform them.

The dependency graph and capability registry are where this object meets
the [WorkGraph](../) and the [authorization matrix](../../autonomy-and-orchestration/):
the domain model says what exists and what can be done to it; the graph
says what work is; the matrix says who may do it.

## Why the vertical platforms close the loop first

This is the mechanism behind the audit's observation that Salesforce,
ServiceNow, UiPath, and Recursion beat general agents at their own games.
They are not better agents; they already *own the domain model*. The
object hierarchy, the system of record, the historical cases, and the
business APIs are prebuilt — the agent inherits a represented world. Data
mesh makes the same point at the data layer
([Zhamak Dehghani's four principles](https://www.martinfowler.com/articles/data-monolith-to-mesh.html)):
domain-owned data products with explicit ownership, so "who owns this
fact" is an answerable question instead of a guess. A general agent has to
build or discover all four parts; a vertical platform hands them over.

The honest consequence for this tutorial: the delivery-stack chapters
cannot fully implement a domain model for a general world — that is
exactly the part a vertical platform supplies. What they can do is show
the shape, which is what this chapter does.

## What the mission already proves

The mission's world is small enough to represent fully, and its mechanics
are the same four parts: the task record is the capability registry (only
the listed tools and files are reachable), the path jail is the
authorization boundary, the mined task set is the dependency graph, and
the repository is the single system of record. The demo of a minimal
domain model would be a small ontology over the mission's own artifacts —
entities (task, file, test), the authoritative store (the task record),
and the dependency edges (shared files from the decomposer's lanes). That
is a planned demo, not a claimed result, and the chapter says so instead
of pretending.

## What this does not say

It does not claim a general domain ontology exists — that is the open
problem, and the vertical platforms win precisely by refusing it. It does
not claim the four parts are sufficient; it claims they are the *naming*
of what the agent must not guess. And it does not claim the mission's
repository model is a delivery domain model — it is the smallest honest
instance, which is exactly why it can be held in one chapter.

**Next:** the agent knows what exists. The next object is what happens
when acting on it fails midway — [side-effect-semantics](../side-effect-semantics/).
