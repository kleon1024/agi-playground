---
status: verified
level: applied
base: scratch
label: When the query is short
verified: 2026-08-06
---

# One word, many intents

**Question:** [stage 10's query understanding](../) classifies intent. This
chapter reads the executed classifier over single-word queries and asks
where it runs out of signal.

**Before this:** [stage 10 — query understanding](../) and its executed
pipeline.

## The queries, executed

The run ([record](runs/2026-08-06-short-query.md)) executes the classifier
over five one-word queries — 'shoes', 'iphone', 'flight', 'headphones',
'fix' — and every one normalizes to a single token with no intent signal.

## Two readings

**A one-word query classifies trivially and ambiguously.** 'shoes' could
be navigational (the category page), transactional (buy shoes), or
informational (which are best) — the stage's rules would label it
navigational by default, but the label says little about what the user
wants.

**The classifier needs more signal than the query.** Previous queries,
device, time, and the user's history all disambiguate 'shoes' in a way
the token alone cannot. A production query-understanding stage combines
the query with context — or deliberately hedges the ranking across
intents, showing both the category and the "best of" list. The short
query is the boundary case where the pipeline's assumptions are exposed.

## Evidence boundary

The executed classifier over five hand-built one-word queries
(illustrative, deterministic). It demonstrates the ambiguity; real
disambiguation needs context features from a user's history.

## Check your mental model

Answer each before opening it.

**1. Why does 'shoes' not classify cleanly?**

<details>
<summary>Answer</summary>

Because the intent is carried by surrounding context, not the word. A
rule-based classifier sees one token and one default label; what the user
actually wants depends on why they typed it — window shopping, a specific
purchase, or comparison. The word is the same in all three cases, so the
classification must come from elsewhere.

</details>

**2. What would a production stage do differently?**

<details>
<summary>Answer</summary>

Combine the query with context — recent queries, device, session
duration, historical intents — and score each intent's probability rather
than picking one label. When the signal is genuinely absent, it hedges:
return a slate that covers the plausible intents instead of betting on
one. The single-word case is where that hedging becomes necessary rather
than optional.

</details>

## Next

Back to [stage 10](../), or to
[where normalization stops and correction must begin](../when-the-query-is-misspelled/)
for the spelling boundary.
