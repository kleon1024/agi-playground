---
status: verified
level: applied
base: scratch
label: Conversational search
verified: 2026-08-07
---

# The session is the other half of the query

**Question:** every search stage so far treated the query as a
self-contained string. This stage asks what changes when the query is a
turn in a conversation and answers: the follow-up is ambiguous alone,
and the session — not the query — is what resolves it.

**Before this:** [stage 10 — query understanding](../10-query-understanding/)
for turning a raw string into intents, and [stage 37 —
LLM query understanding](../37-llm-query-understanding/) for the
LLM-parsed key space this session augments.

## The resolution, executed

The run ([record](runs/2026-08-07-conversational-search.md)) scores the
follow-up "what about the cheaper ones" with and without context:

| candidate intent | with context | without |
|---|---:|---:|
| cheaper marathon shoes | 0.8 | 0.2 |
| cheaper headphones | 0.1 | 0.6 |
| cheaper laptops | 0.1 | 0.2 |

Resolved: cheaper marathon shoes.

## The mechanism, named

The first turn establishes the topic — marathon running shoes. The
follow-up says "cheaper ones", which names no product; without the
session it could be shoes, headphones, or laptops. With the session the
resolution shifts to the cheaper marathon shoes (0.8). The query is
only part of the input; the session is the other part, and
conversational search is the mechanism that carries it.

## Why this belongs in the mission

Search's raw input is becoming conversational — voice assistants,
chat-first products, multi-turn refinement. That changes the query
understanding contract stage 10 built: the key space is now resolved
across turns, not per string. The mission's frontier claim is that the
funnel survives the new input; the topic-shift and anaphora detours
show the two ways session context can fail, which the search frontier
has to handle before it can claim the funnel still works.

## Evidence boundary

The executed resolution over two declared turns with assumed intent
scores (illustrative, deterministic). It demonstrates the mechanism;
real conversational search needs the session model, the intent space,
and measured resolution quality, which an online experiment would
estimate.

## Check your mental model

Answer each before opening it.

**1. Why is the follow-up alone ambiguous?**

<details>
<summary>Answer</summary>

Because "cheaper ones" names no product — the noun is missing. Without
context the model spreads probability across shoes, headphones, and
laptops, and the most likely candidate depends on the prior. The first
turn ("best running shoes for marathons") is what makes "ones" mean
shoes, which is why the session has to be part of the input.

</details>

**2. What does the session contribute that the last query alone
cannot?**

<details>
<summary>Answer</summary>

The topic and the referents. The last query supplies the words; the
session supplies what those words point at — the product category, the
entities mentioned earlier, the constraint history. The executed run
shows the difference directly: with context the cheap-marathon-shoes
intent scores 0.8, without it 0.2.

</details>

## Next

The frontier search track continues. Next is [stage 37 — LLM query
understanding](../37-llm-query-understanding/), where a raw string
becomes a structured key space.

A detour from here: [the topic shifts and the old context goes
stale](when-the-topic-shifts/) — the executed read: after the session
switches to hotels, "near shibuya" is still read against marathon shoes,
so a topic boundary has to expire old context.

Another detour: [the anaphora is ambiguous between two
referents](when-the-anaphora-is-ambiguous/) — the executed read:
"they" could be trail runners or road trainers, and resolving it wrong
changes the answer, so search has to track referents, not reuse the last
query.
