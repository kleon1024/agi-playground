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

## How you find it: the resolution-stability audit, executed

The failure mode this audit exists for is the aggregate resolution
metric: a short-session-dominated log reports "conversational search
resolves well" while long sessions — where truncation drops the
first-turn grounding — lose most of their resolution. The run
([record](runs/2026-08-07-session-audit.md)) emits a 10-session log and
stratifies resolution by session length:

| stratum | sessions | mean turns | resolution |
|---|---:|---:|---:|
| head | 5 | 3.2 | 0.980 |
| tail | 5 | 17.8 | 0.380 |

The verdict is RESOLUTION LOST IN LONG SESSIONS: the aggregate
resolution of 0.680 is a short-session artifact — sessions of 2-4 turns
resolve at 0.980, sessions of 12-24 turns at 0.380. Truncation drops
the oldest turns first, and the first-turn topic is exactly the
grounding a follow-up that says "back to the first pair" needs (the
long-context shape "Lost in the Middle" measures; Liu et al., TACL
2024). The decision that follows: pin the first-turn grounding or
compress the middle turns so the referent survives the window.

## Who owns the loop

The session is the resolution surface's input, and the handoffs are
where the grounding gets lost:

- **The conversational-search or assistant team** owns the session
  itself: the context window, the retention policy, and the
  resolution metric per session length — the
  [when-the-context-is-long detour](when-the-context-is-long/) is its
  failure mode.
- **The query-understanding team** owns the referent resolution: which
  candidate an anaphora picks when the session offers two — the
  [when-the-anaphora-is-ambiguous detour](when-the-anaphora-is-ambiguous/)
  is its failure mode.
- **The product owner** owns the session contract: when a topic shift
  expires old context, and what "still the same conversation" means to
  the user — the [when-the-topic-shifts
  detour](when-the-topic-shifts/) is its pricing.

When the ownership is implicit, the assistant team measures a short
session, the understanding team resolves the last query, and nobody
owns the long session — so the grounding loss ships as "conversational
search resolves well" until resolution is stratified by session length.

## Why this belongs in the mission

Search's raw input is becoming conversational — voice assistants,
chat-first products, multi-turn refinement. That changes the query
understanding contract stage 10 built: the key space is now resolved
across turns, not per string. The mission's frontier claim is that the
funnel survives the new input; the three detours show the ways session
context can fail, which the search frontier has to handle before it can
claim the funnel still works.

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

And a third: [the context is long and the first turn falls out of the
window](when-the-context-is-long/) — the executed sweep read:
resolution of "back to the first pair" falls from 1.0 at 8 turns to
0.1 at 24, so truncation drops the first-turn grounding that the
follow-up needs.
