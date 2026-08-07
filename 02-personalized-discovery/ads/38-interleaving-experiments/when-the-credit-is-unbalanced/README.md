---
status: verified
level: applied
base: scratch
label: When the credit is unbalanced
verified: 2026-08-07
---

# The credit is unbalanced when both teams proposed the click

**Question:** [stage 38's interleaving](../) credits clicks to the team
that proposed each result. This chapter reads the executed tie and asks
what happens when both teams proposed the clicked document.

**Before this:** [stage 38 — interleaving experiments](../) and its
executed blended-list credit model.

## The tie, executed

The run ([record](runs/2026-08-07-credit-is-unbalanced-read.md)) checks
the clicked document against both rankings:

| team | proposed list | contains d2 |
|---|---|---|
| a | d1, d2, d3 | True |
| b | d2, d4, d5 | True |

Clicked: d2.

## The reading

d2 appears in both rankings, so the click's credit is ambiguous — both
teams proposed it, and neither can claim the click alone. Interleaving
credit needs a tie rule (first proposal, random split), or the shared
documents silently blur the comparison: a click on common content
credits both teams, and the experiment reports a difference the teams
did not cause. The tie rule is what keeps the credit honest.

## Evidence boundary

The executed check over one declared click (illustrative, deterministic,
assumed rankings). It demonstrates the mechanism; real interleaving
needs the blending algorithm, the tie rule, and a statistical test over
many credits.

## Check your mental model

Answer each before opening it.

**1. Why is a click on d2 not a clean signal for either team?**

<details>
<summary>Answer</summary>

Because d2 is common content — both rankings proposed it. The click
could mean the user liked the result, or the position, or the team that
happened to place it higher; it cannot be attributed to one team's
ranking change. Without a tie rule the click counts for both, and the
credit sum no longer reflects which ranking the user actually
preferred.

</details>

**2. What does the tie rule decide, and why does it matter?**

<details>
<summary>Answer</summary>

It decides which team owns a click on shared content — first proposal,
random split, or exclusion. The choice changes the credit totals and
can flip the experiment's winner, so it has to be declared before the
run and applied consistently. A tie rule that is implicit or random
under the hood makes the comparison's result a property of the rule,
not of the rankings.

</details>

## Next

Back to [stage 38](../). The
[tiny-traffic detour](../when-the-traffic-is-tiny/) shows why
interleaving exists at all: the A/B that needs ten thousand users.
