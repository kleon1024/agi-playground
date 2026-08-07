---
status: verified
level: applied
base: scratch
label: Personalized search
verified: 2026-08-07
---

# Same query, two users, two orders

**Question:** every stage so far ranked for a query with no user
attached. This stage asks what the user's history adds, and answers:
context over the query's meaning — same query, two users, two orders.

**Before this:** [stage 12 — search ranking](../12-search-ranking/) for
the ranking being personalized, and [stage 00 — interactions](../../shared/00-interactions/)
for where the user history comes from.

## The personalization, executed

The run ([record](runs/2026-08-07-personalized-search.md)) scores the
query `running shoes` against the same three documents for two users
with different affinity vectors:

| user | top of list | order |
|---|---|---|
| A | trail runners | trail runners, road trainers, track spikes |
| B | track spikes | track spikes, road trainers, trail runners |

Relevance is identical; only the affinity vector differs, and the top
slot flips.

## The mechanism, named

Personalized search scores each document as relevance plus affinity:
what the query says plus what the user's history says. The run makes
the division explicit — the query and relevance scores never change,
and the order still flips. Personalization is context added to the
query; its risk is that the context overrides the query's actual
intent, which the [over-personalization detour](when-personalization-hurts/)
measures.

## Why this belongs in the mission

This is where the mission's central claim becomes visible: search and
recommendation are the same decision loop. Recommendation ranks with no
query; search ranks with one. Personalized search is the bridge — the
explicit query plus the user's history, which is exactly the
interaction data [stage 00](../../shared/00-interactions/) cleaned and split.

## Evidence boundary

The executed ranking over three hand-built documents and two affinity
vectors (illustrative, deterministic). It demonstrates the mechanism;
real personalization also needs measured history quality and
guardrails against narrowing — the mission's cold-start and coverage
guardrails apply to search as much as to recommendation.

## Check your mental model

Answer each before opening it.

**1. What exactly changed between the two users?**

<details>
<summary>Answer</summary>

Only the affinity vector. Relevance scores are identical and the
documents are identical — the entire ordering flip comes from user
context. That is the point and the danger: the context is powerful
enough to decide the ranking, so the model has to treat it as a prior
over the query's meaning, not a replacement for it.

</details>

**2. When should the query beat the history?**

<details>
<summary>Answer</summary>

When the history is narrower than the intent. If the user's history is
all trail running and they search `shoes` broadly, personalization can
hide dress shoes, hiking boots, and slippers — the
[over-personalization detour](when-personalization-hurts/) executes
exactly that coverage loss. The query's own signal has to win
sometimes.

</details>

## Next

Forward to [stage 24 — search measurement](../24-search-measurement/)
where the search track's outcome is measured.

A detour from here: [history is a prior over the query](when-the-user-history-helps/) — the executed disambiguation read: `apple` alone
could be fruit or phone, and a phone-heavy history lifts the support
intent to 0.9 against 0.4 and 0.3, which is exactly what personalization
adds.

Another detour: [history can hide what the query asked
for](when-personalization-hurts/) — the executed coverage read: the
broad `shoes` result covers four categories while the personalized
result narrows to trail running, so the query's signal must win when
intent is broader than history.
