---
status: verified
level: applied
base: scratch
label: When the topic shifts
verified: 2026-08-07
---

# The topic shifts and the old context goes stale

**Question:** [stage 36's conversational search](../) resolves follow-ups
with session context. This chapter reads the executed stale-context
failure and asks when the context should expire.

**Before this:** [stage 36 — conversational search](../) and its executed
session-context model.

## The shift, executed

The run ([record](runs/2026-08-07-topic-shifts-read.md)) carries a
session across a topic change:

| turn | query | resolved intent |
|---|---|---|
| 1 | running shoes | search_marathon |
| 2 | what about the cheaper ones | search_marathon |
| 3 | actually, book a hotel in tokyo | search_hotel |
| 4 | any good ones near shibuya | search_marathon (stale) |

## The reading

The fourth query is about hotels — "near shibuya" extends the hotel
turn — but the session context still points at marathon shoes, so the
resolution is stale: search_marathon instead of search_hotel. The
context that helped turn 2 became the trap by turn 4. Conversation
needs a topic boundary: when the intent class changes, the old context
has to expire, or every follow-up after the shift is resolved against
the wrong topic.

## Evidence boundary

The executed resolution over one declared four-turn session
(illustrative, deterministic, assumed intent transitions). It
demonstrates the mechanism; real conversational search needs the topic
model and measured resolution quality over real sessions.

## Check your mental model

Answer each before opening it.

**1. Why did the context help turn 2 but hurt turn 4?**

<details>
<summary>Answer</summary>

Because the topic changed between them. Turn 2's "cheaper ones" needs
the marathon context to resolve — without it, "ones" is ambiguous. Turn
3 declares a new topic (hotels), so turn 4's "near shibuya" should
resolve against hotels. The same mechanism that disambiguates the
follow-up also anchors it to the old topic, and nothing in the model
decided the anchor was stale.

</details>

**2. What is the topic boundary, and what does it need to detect?**

<details>
<summary>Answer</summary>

It is the rule that expires context when the intent class changes. It
needs to detect the shift — turn 3's intent, search_hotel, differs from
the session's marathon topic — and reset the context store so
subsequent turns resolve against the new topic. Without the boundary,
conversational search is correct only until the first topic change,
which is exactly the failure the executed session shows.

</details>

## Next

Back to [stage 36](../). The
[anaphora detour](../when-the-anaphora-is-ambiguous/) shows the other
session failure: a referent that was never ambiguous before the
follow-up.
