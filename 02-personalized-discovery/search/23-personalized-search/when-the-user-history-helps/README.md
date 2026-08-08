---
status: verified
level: applied
base: scratch
label: When the user history helps
verified: 2026-08-07
---

# History is a prior over the query

**Question:** [stage 23's personalized search](../) adds user context
to the ranking. This chapter reads the executed disambiguation case and
asks when history genuinely helps.

**Before this:** [stage 23 — personalized search](../) and its executed
relevance-plus-affinity model.

## The disambiguation, executed

The run ([record](runs/2026-08-07-history-helps-read.md)) scores
documents for the query `apple` given a phone-heavy history:

| document | score |
|---|---:|
| apple store support | 0.9 |
| fruit recipes | 0.4 |
| apple pie recipe | 0.3 |

History: `iphone battery`, `iphone cases`.

## The reading

`apple` alone could be fruit or phone; the phone-heavy history lifts the
support intent to 0.9 against 0.4 and 0.3. History is a prior over the
query's meaning, and the prior is what personalization adds. The query
still decides the candidate set — the history decides which reading of
the query the user most likely meant.

## The fix and its trade

The fix is to treat history as a prior over the query's meaning, with
measured history quality — the query still decides the candidate set,
and the history decides which reading the user most likely meant. The
executed disambiguation prices the mechanism: `apple` with a phone-heavy
history (iphone battery, iphone cases) scores apple store support 0.9
against fruit recipes 0.4 and apple pie recipe 0.3 — the prior lifts the
intended reading without changing what the query could retrieve.

The trade, named: history buys disambiguation at the price of history
quality — a noisy or stale history weakens the prior it provides, and a
stale one is stage 46's expiry in a different artifact, quietly shifting
the reading of every ambiguous query. The boundary is the same as the
over-personalization detour: the prior must stay a prior, because the
moment it overrides the query's candidate set, personalization becomes
a filter.

## Who owns the loop

- **The personalization model team** owns the history features and the
  prior's strength per query class.
- **The data team** owns history freshness and quality — a stale history
  is a weak or wrong prior.
- **The evaluation team** owns the disambiguation read that shows the
  prior lifting the intended reading without hiding alternatives.

## Evidence boundary

The executed scoring over three hand-built documents and one declared
history (illustrative, deterministic). It demonstrates the mechanism;
real history quality is measured per user, and a noisy or stale history
weakens the prior it provides.

## Check your mental model

Answer each before opening it.

**1. What exactly does the history add to the query?**

<details>
<summary>Answer</summary>

A prior over meaning. The query `apple` is ambiguous; the history says
this user's recent intent has been phone-related, so the support
reading wins. Without the history the ranking has no way to choose a
sense; with it, the choice is the personalization.

</details>

**2. When would this same mechanism hurt?**

<details>
<summary>Answer</summary>

When the prior is wrong — a user whose history is stale, or whose intent
is broader than their history. The same lift that resolves ambiguity
can override a query the user meant broadly; the
[over-personalization detour](../when-personalization-hurts/) shows
that coverage loss.

</details>

## Next

Back to [stage 23](../), where the ranking gains a user. The
[over-personalization detour](../when-personalization-hurts/) shows the
same lever failing.
