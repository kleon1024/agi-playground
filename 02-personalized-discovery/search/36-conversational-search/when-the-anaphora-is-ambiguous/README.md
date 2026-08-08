---
status: verified
level: applied
base: scratch
label: When the anaphora is ambiguous
verified: 2026-08-07
---

# The anaphora is ambiguous between two referents

**Question:** [stage 36's conversational search](../) tracks the session.
This chapter reads the executed referent check and asks what happens
when the pronoun has two candidates.

**Before this:** [stage 36 — conversational search](../) and its executed
session-context model.

## The ambiguity, executed

The run ([record](runs/2026-08-07-anaphora-is-ambiguous-read.md)) checks
one follow-up against the session:

| entity | "they" resolves to |
|---|---|
| trail runners | plausible |
| road trainers | ambiguous |

## The reading

"they" is ambiguous between two shoe types mentioned in the session.
Both are valid referents, and resolving it wrong changes the answer —
"are they waterproof" against trail runners is a different question
than against road trainers. Conversational search has to track
referents, not just reuse the last query: the last query named both
entities, so it provides no resolution. The model has to decide which
referent the pronoun points at, and an ambiguous session makes that
decision unsafe to guess.

## The fix and its trade

The fix is to track referents, not just reuse the last query, and to make
the resolution safe to guess — when the session offers two valid
referents, the system must ask. The executed ambiguity prices the
failure: "they" resolves plausibly to trail runners and ambiguously to
road trainers — both were named in the session — and resolving it wrong
changes the answer: "are they waterproof" against trail runners is a
different question than against road trainers. The last query named
both entities, so it provides no resolution at all.

The trade, named: a coreference model costs training data and serving
latency, and the clarification policy costs a turn — but guessing on an
ambiguous session is the failure that converts a cheap answer into a
wrong one. The system that cannot decide which referent a pronoun
points at must say so, because the alternative is a confident answer to
a question the user did not ask.

## Who owns the loop

- **The query-understanding team** owns referent resolution and its
  ambiguity detection.
- **The assistant team** owns the clarification policy — when to ask
  instead of guess, and how the ask is phrased.
- **The evaluation team** owns the resolution-quality read over real
  sessions, including the ambiguous ones.

## Evidence boundary

The executed check over one declared session (illustrative,
deterministic, assumed entities). It demonstrates the mechanism; real
conversational search needs the coreference model and measured
resolution quality over real sessions.

## Check your mental model

Answer each before opening it.

**1. Why does reusing the last query fail here?**

<details>
<summary>Answer</summary>

Because the last query introduced both candidates. "they" needs a
single referent, and the last query gives the model two — trail runners
and road trainers — with no signal about which one the pronoun means.
Reusing the query is only sufficient when the query names one thing;
with two candidates the model has to do coreference resolution, and the
ambiguity is real.

</details>

**2. What is the cost of resolving it wrong?**

<details>
<summary>Answer</summary>

The answer changes. "Are they waterproof" asked about trail runners and
about road trainers are different questions with potentially different
answers — one may be waterproof and the other not. The wrong resolution
produces a confident answer to the wrong question, which is worse than
asking for clarification, because the user cannot see the model resolved
the pronoun against the other shoe.

</details>

## Next

Back to [stage 36](../). The
[topic-shift detour](../when-the-topic-shifts/) shows the failure on
the other axis: context that is clear but stale.
