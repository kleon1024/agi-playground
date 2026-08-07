---
status: verified
level: applied
base: scratch
label: When personalization hurts
verified: 2026-08-07
---

# History can hide what the query asked for

**Question:** [stage 23's personalized search](../) adds user context
to the ranking. This chapter reads the executed coverage-loss case and
asks when the context should lose to the query.

**Before this:** [stage 23 — personalized search](../) and its executed
relevance-plus-affinity model.

## The coverage loss, executed

The run ([record](runs/2026-08-07-over-personalize-read.md)) ranks the
same query `shoes` with and without a trail-running history:

| ranking | result set |
|---|---|
| broad | running shoes, dress shoes, hiking boots, slippers |
| personalized | trail runners, running shoes, trail shoes, trail boots |

## The reading

The history pushes the result set toward trail running, shrinking
coverage from four categories to one. When the user's intent is broader
than their history, personalization hides relevant results — dress
shoes, hiking boots, and slippers are gone. The query's own signal has
to win sometimes: personalization is a prior over meaning, and a prior
that overrides the query stops being a prior and becomes a filter.

## Evidence boundary

The executed comparison over one query and one declared history
(illustrative, deterministic). It demonstrates the failure mode; real
systems guard coverage per query class, which is the mission's catalogue
coverage guardrail applied to search.

## Check your mental model

Answer each before opening it.

**1. Why does the broad result cover more than the personalized one?**

<details>
<summary>Answer</summary>

Because the query `shoes` is broad, and the broad ranking expresses
that breadth. The history narrows the reading to trail running, which
matches the prior but not the query. Coverage is the cost of
over-confident context: four categories collapse to one.

</details>

**2. How does the system decide when the query should win?**

<details>
<summary>Answer</summary>

By measuring coverage per query class and guarding it — the mission's
guardrails already require catalogue coverage not to fall below the
baseline. When personalization narrows a broad query's result set, that
guardrail is the tripwire: the query's signal has to beat the history
for queries where the history is a weak prior.

</details>

## Next

Back to [stage 23](../), where the ranking gains a user. The
[history-helps detour](../when-the-user-history-helps/) shows the same
lever succeeding on an ambiguous query.
