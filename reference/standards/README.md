---
level: reference
---

# Standards

The contracts everything else in this repo has to satisfy. Read these before
adding a lesson, a capability, or a mission.

| Document | What it governs |
|---|---|
| [`mission-contract.md`](mission-contract.md) | What a mission must declare before it is built, how outcomes are proven when they cannot be run, and the gate a capability must pass to enter the curriculum |
| [`lesson-and-run-contract.md`](lesson-and-run-contract.md) | Lesson anatomy, what a run record must contain, `status:` semantics, and the rules that exist because they were broken first |

## The two invariants

> **Every capability claim is backed by a run.**
> **Every mission is backed by a measurable outcome.**

The first is why technical numbers here are trustworthy: each traces to a
command, a machine, and a wall-clock. The second is the harder one, because
business outcomes cannot be executed on a GPU — so missions prove them against
declared, reproducible proxies and are required to state what they do *not*
establish.

A repository that teaches systems thinking has to hold itself to the standard
it teaches. If an outcome claim here cannot be traced, it should not be here.
