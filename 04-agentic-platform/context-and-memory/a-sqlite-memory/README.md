---
status: verified
level: applied
base: scratch
label: A SQLite memory
verified: 2026-08-14
---

# Six facts the mission actually measured, recalled and promoted

**Question:** the stage claims memory is a two-layer system — a static
instruction file and a generated layer of what the agent itself learned —
and that promotion should follow use, not sentiment. Can a 150-line SQLite
store demonstrate both on real data?

**The artifact this chapter follows** is the store's snapshot: six lessons
seeded from this mission's own `runs/` records, two decision questions
recalled against them, and the promotion that a second recall triggers. The
record ([JSON](runs/2026-08-14-sqlite-memory.json)) is real — every seeded
claim names the `runs/` file that measured it, and no model was called.

By the end you will be able to say what a keyword store can and cannot do,
and why production memory moved to vector retrieval while keeping exact
facts in stores exactly like this one.

**Before this:** the stage's two-layer claim. This chapter is its
smallest working instance.

## What the store holds

The six seeded lessons are the mission's measured findings, each with its
source file: haiku's 0/6 blind-call resolve, the guardrail that fires only
on the diff, the 18/18 harness resolve with latent defects the metric
cannot see, the 0/12-to-2/12 feedback result, the 11-of-12 patch-apply
failures, and the never-firing taxonomy row.

## The two recalls, read

```text
question 1: "which tier should resolve it; what does the blind-call say?"
  recalled: lessons 1 (tier baseline), 3 (routing), 4 (feedback)
  promoted: none yet

question 2: "is the resolve rate still believable when nothing failed?"
  recalled: lessons 1, 4   ->  both promoted to durable
```

Lesson 1 (the tier/resolve facts) is recalled by both questions and becomes
`durable`; lesson 4 (the feedback result) does the same. Lesson 2 — the
guardrail claim — is recalled by neither, because neither question mentions
guardrails or tampering. That is the whole point of the two-layer split: the
store does not decide what matters, recall does. A fact that is never
recalled stays ephemeral, and an unpruned instruction file is exactly a
store where everything is durable because nothing is ever filtered.

## What this proves and what it does not

It proves the mechanics: write, recall, promote-on-second-use are real
operations on real data, and `LIKE` keyword matching is visibly too weak for
open-ended questions — "is the resolve rate still believable" only matched
lessons whose keywords happened to co-occur. That is why the industry layer
above this (Mem0's fact extraction, Zep's temporal graphs) exists, and why
Codex pairs the generated layer with an AGENTS.md instruction layer rather
than trusting recall alone.

It does not prove memory improves resolve rate. The mission's
`closing-the-loop` stage measured the one-loop version of that question
(0/12 to 2/12); scaling that across sessions is a dated-survey claim in the
stage, not a number this chapter produces.

**Next:** [memory tiers](../) — the full production stack this store is one
cell of.
