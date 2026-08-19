---
status: draft
level: frontier
base: none
label: Side-effect semantics
---

# The agent acts; the machine may run that act twice. What does acted mean then?

**Question:** the runtime stage established that durable execution is
at-least-once: an external side effect can happen twice. This chapter makes
that concrete for the delivery stack. An agent that writes a file,
installs a package, deploys a service, or sends a message is producing
side effects — and every one of them has a delivery semantic that the
harness's test runs never had to face, because running pytest twice is
harmless and deploying twice is not.

**The artifact this chapter follows** is the classification itself: the
side effects a delivery agent produces, sorted by what happens when they
run twice, with the mechanism each class requires. The mission's test
commands are the harmless end; deployment is the dangerous end.

**Before this:** [runtime-and-durability](../../runtime-and-durability/)
established at-least-once and why the journal alone is not enough. This
chapter is the full semantics of the problem.

## Why the harness never saw this

The mission's loop runs pytest, reads files, writes patches. Every one of
those is idempotent: running it twice produces the same result and no
lasting harm. The checkpoint demo's "completed work, not position" rule
works precisely because the work is redo-safe. Delivery is not:

| Side effect | Twice is... | Mechanism |
|---|---|---|
| read a file | harmless | none needed |
| run a test | harmless (if the test is deterministic) | none needed |
| write a patch | mostly harmless — the second write overwrites | idempotent write |
| install a package | harmless if versioned, harmful if unpinned | pin + check |
| call a payment API | harmful — charged twice | idempotency key |
| deploy a service | harmful — a second deploy can race the first | deployment gate + rollback |
| send a customer message | harmful — the customer sees two | outbox + dedup |
| append to an audit log | harmful — the record lies | unique constraint |

The line between the top and bottom of the table is the line between a
harness and a delivery system. Everything above the line, the mission
already does; everything below it is what a delivery stack must add.

## The semantics, precisely

Three delivery guarantees, and the system must *state which one each
effect has* rather than assuming:

- **At-least-once** — the effect ran at least once; it may have run more.
  This is the default of every retrying runtime, including Temporal
  Activities. Safe only for idempotent effects.
- **At-most-once** — the effect ran at most once; it may have run zero
  times. Achieved by disabling retries, which trades reliability for
  safety — a crashed call is simply lost.
- **Exactly-once** — the effect ran exactly once. This is not a primitive
  any external system provides; it is *constructed* from at-least-once
  delivery plus idempotent consumption ([MassTransit's outbox
  documentation](https://masstransit.massient.com/concepts/outbox) is a
  precise statement of why: at-least-once delivery plus a deduplicating
  inbox yields exactly-once consumer behavior).

Exactly-once is a theorem about two components, not a property of one
transport. The delivery stack's job is to know which of the three each
side effect is under, and to build the machinery that upgrades the ones
that need upgrading.

## The machinery, and when each piece applies

Four patterns cover the table's dangerous rows
([transactional outbox](https://vibgrate.com/patterns/transactional-outbox-pattern/)
and Saga are the standard references):

| Pattern | What it does | When it applies |
|---|---|---|
| Idempotency key | the caller sends a key; the callee returns the stored result for a repeated key | a non-idempotent external call (payment, message) |
| Transactional outbox | the side effect's record and the trigger commit in the same transaction; a relay publishes later | the effect and its bookkeeping must not diverge |
| Saga compensation | every step has a compensating step; a failure walks the steps back | a multi-step effect where a partial result is dangerous |
| Reconciliation | a periodic job compares intended state with actual state and repairs drift | effects whose delivery is best-effort and whose state is queryable |

The outbox row deserves the emphasis, because it is the one that converts
the runtime stage's journal into a delivery guarantee: the workflow may be
journaled, but the *external* call is only safe if its record commits with
the state change that caused it, or a crash between the two produces a
side effect with no bookkeeping — the exact failure the runtime chapter
named.

## Two failures that are not in the table

Workflow version migration and stale authorization sit outside the
semantics table and break deliveries anyway. A workflow definition that
changes mid-flight produces a replay that mixes old and new logic — the
delivery system must version its graphs and decide, per running instance,
whether to migrate, abandon, or complete under the old version. And an
authorization granted at start is not valid at the end: a long delivery
must re-check authority against current policy before each consequential
action, or a permission revoked mid-delivery is silently exercised.
Both are the same disease as the table's rows — state that the agent
assumed stable while the world moved — and both are why the delivery
stack keeps its own state (the RunLedger) rather than trusting the
agent's memory of what it was allowed to do.

## What this does not say

It does not claim the mission's harness needs any of this — its effects
are all above the table's line, which is why the checkpoint demo works.
It does not claim exactly-once is achievable in general; it claims
exactly-once is *constructible* where the effect is idempotent or
deduplicable, and that the system must know which case it is in. And it
does not claim these four patterns are the whole of distributed-systems
practice — they are the subset a delivery agent actually hits, which is
the point of naming them.

**Next:** side effects need a boundary around them. The next object is
what that boundary is made of — [trust-boundaries](../trust-boundaries/).
