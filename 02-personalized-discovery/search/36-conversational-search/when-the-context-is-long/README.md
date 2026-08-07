---
status: verified
level: applied
base: scratch
label: When the context is long
verified: 2026-08-07
---

# The context is long, and the first turn falls out of the window

**Question:** [stage 36's conversational search](../) resolves follow-ups
through session context. This chapter asks what happens when the session
grows past the context window, and answers: truncation drops the oldest
turns first, so the first-turn grounding — the topic the whole session
is about — is the first thing lost.

**Before this:** [stage 36 — conversational search](../), and the
[topic-shift detour](../when-the-topic-shifts/) for the context
expiration that is the other failure of a growing session.

## The window, executed

The run ([record](runs/2026-08-07-long-context-read.md)) grows a session
from 4 to 24 turns against a window of 8:

| session turns | turn-1 kept | resolution of "back to the first pair" |
|---|---:|---:|
| 4 | yes | 1.0 |
| 8 | yes | 1.0 |
| 9 | no | 0.8 |
| 12 | no | 0.2 |
| 24 | no | 0.1 |

## The reading

Truncation is oldest-first: when the session passes the window, the
first turn is the first thing dropped. But the first turn is not
expendable — it sets the topic, and a follow-up that says "back to the
first pair" or "the ones from turn one" needs exactly that grounding.
Resolution falls from 1.0 to 0.1 as the dropped grounding recedes. This
is the long-context shape that "Lost in the Middle" measures (Liu et
al., TACL 2024): models use the beginning and end of a long input far
better than the middle, so where the grounding sits decides whether it
resolves. Radlinski and Craswell's conversational-search framework
(CHIIR 2017) makes the same point from the other side: the conversation
state is the shared context, and losing part of it changes what a
follow-up can mean. The production fix is not a bigger window — it is
deliberate retention: pin the first-turn grounding (a standing summary
of the session topic), or compress the middle turns instead of dropping
the oldest, so the referent survives the window.

## Evidence boundary

The executed window sweep over declared resolution values
(illustrative, deterministic). It demonstrates the shape; real
resolution loss needs the actual session log, the real window size, and
measured resolution per session length.

## Check your mental model

Answer each before opening it.

**1. Why is the first turn the worst turn to drop?**

<details>
<summary>Answer</summary>

Because it carries the topic. Every follow-up resolves against what the
session is about, and that is established in the first turn. Dropping
the most recent turn loses little — its content is usually repeated or
superseded — but dropping turn one removes the anchor, so "back to the
first pair" has nothing to resolve against.

</details>

**2. Why is a bigger window not the answer?**

<details>
<summary>Answer</summary>

Because the failure is positional, not size-based. "Lost in the Middle"
shows that models use the beginning and end of a long input far better
than the middle, so a longer window just moves the grounding into the
weak zone. Retention is the fix: pin the first-turn grounding or
compress the middle turns, so the referent stays reachable regardless
of window size.

</details>

## Next

Back to [stage 36](../). The
[anaphora detour](../when-the-anaphora-is-ambiguous/) shows the other
failure of session resolution: a referent that is present in context
but ambiguous between two candidates.
