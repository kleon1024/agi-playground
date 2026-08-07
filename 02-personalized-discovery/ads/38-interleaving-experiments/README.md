---
status: verified
level: applied
base: scratch
label: Interleaving experiments
verified: 2026-08-07
---

# Compare rankings with one blended list

**Question:** every measurement stage so far compared groups of users.
This stage asks how to compare two rankings with a fraction of the
traffic and answers: interleaving — both users see one blended list,
and clicks credit the team that proposed each clicked result.

**Before this:** [stage 24 — search measurement](../../search/24-search-measurement/)
for the offline-versus-online gap, and [stage 30 —
ads measurement](../30-ads-measurement/) for the control-group
discipline interleaving replaces with a within-user comparison.

## The credit, executed

The run ([record](runs/2026-08-07-interleaving-experiments.md))
interleaves two teams' rankings:

| team | proposed list |
|---|---|
| a | d1, d2, d3 |
| b | d4, d2, d5 |
| interleaved | d1, d4, d2, d3, d5 |
| clicks | d4, d2 |
| credit | team a 1, team b 2 |

## The mechanism, named

Both teams propose a ranking; the system blends them into one list and
shows every user the same interleaved list. Each click credits the team
that proposed the clicked result — d4 credits b, d2 credits a, so b
wins on its exclusive proposal. Because both ranking variants appear
inside the same user session, the comparison cancels user-level noise,
which is why interleaving needs far fewer users than a between-user
A/B.

## Why this belongs in the mission

The mission's funnel changes ranking constantly, and the old comparison
costs traffic the product cannot spare. Interleaving is how ranking
teams ship changes with limited traffic — the tiny-traffic detour shows
an A/B needs 10,000 users where interleaving needs 400. The frontier
claim is that measurement can be faster without being weaker, and the
credit-tie detour states the one mechanism that must be decided for the
credit to be honest.

## Evidence boundary

The executed interleave over two hand-built rankings with declared
clicks (illustrative, deterministic, assumed click sequence). It
demonstrates the mechanism; real interleaving needs the blending
algorithm, the tie rule, and a statistical test over the credits, which
the detours quantify.

## Check your mental model

Answer each before opening it.

**1. Why does interleaving need far fewer users than a between-user
A/B?**

<details>
<summary>Answer</summary>

Because the comparison happens inside each user's session. A
between-user A/B compares groups, so user-level variance is noise and
the test needs enough users to average it out. Interleaving shows both
variants to the same user, so that variance cancels within each
session — the executed feasibility read: 400 users for interleaving
against 10,000 for the A/B.

</details>

**2. What does the credit rule have to decide before the experiment is
valid?**

<details>
<summary>Answer</summary>

What happens when a clicked document appears in both rankings. d2 was
proposed by both teams, so its credit is ambiguous — the tie rule
(first proposal, random split) decides it. Without the rule, shared
documents silently blur the comparison and the credit misstates which
team caused the click, which is the unbalanced-credit detour's point.

</details>

## Next

This opens the frontier ads track (stages 38-42). Next is [stage 39 —
first-price transition](../39-first-price-transition/), where the
winner pays its own bid.

A detour from here: [the credit is unbalanced when both teams
proposed the clicked document](when-the-credit-is-unbalanced/) — the
executed tie read: d2 is in both rankings, so its click credits both
teams and the comparison blurs unless a tie rule decides.

Another detour: [the traffic is too tiny for a between-user
A/B](when-the-traffic-is-tiny/) — the executed feasibility read: with
800 users the A/B never reaches significance (needs 10,000) while
interleaving needs 400 and ships.
