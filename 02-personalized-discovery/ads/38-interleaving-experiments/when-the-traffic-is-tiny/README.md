---
status: verified
level: applied
base: scratch
label: When the traffic is tiny
verified: 2026-08-07
---

# The traffic is too tiny for a between-user A/B

**Question:** [stage 38's interleaving](../) compares rankings with one
blended list. This chapter reads the executed feasibility check and
asks when interleaving is the only option.

**Before this:** [stage 38 — interleaving experiments](../) and its
executed blended-list credit model.

## The feasibility, executed

The run ([record](runs/2026-08-07-traffic-is-tiny-read.md)) checks two
designs against 800 available users:

| design | users needed | available | feasible |
|---|---:|---:|---|
| between-user A/B | 10,000 | 800 | False |
| interleaving | 400 | 800 | True |

## The reading

With 800 users the A/B never reaches significance — it needs 10,000 to
separate the ranking effect from user-level noise — while interleaving
needs 400 and ships. For a ranking change the unit of comparison is the
list, not the user: interleaving shows both variants to the same user,
cancelling the user-level variance that forces the A/B's sample size.
That is why interleaving is the standard online tool for ranking teams
with limited traffic.

## Evidence boundary

The executed feasibility comparison over two declared sample sizes
(illustrative, deterministic, assumed effect sizes). It demonstrates
the mechanism; real experiment design needs the actual effect size,
variance, and power calculation, which a statistician would run.

## Check your mental model

Answer each before opening it.

**1. Why does the A/B need twenty-five times the users?**

<details>
<summary>Answer</summary>

Because it compares groups of users, and user-level variance is the
noise. Each user has a baseline click tendency unrelated to the ranking,
so the A/B needs enough users for that variance to average out — 10,000
in the executed model. Interleaving shows both rankings to the same
user, so the baseline cancels within each session and 400 users suffice.

</details>

**2. What is the unit of comparison in each design?**

<details>
<summary>Answer</summary>

The user in the A/B, the list in interleaving. The A/B assigns users to
one variant and compares group outcomes; interleaving assigns both
variants to every user and compares the credits their clicks earn. When
the change under test is a ranking, the list is the natural unit, which
is why interleaving's smaller sample fits the question it answers.

</details>

## Next

Back to [stage 38](../). The
[credit-tie detour](../when-the-credit-is-unbalanced/) shows the rule
that keeps interleaving's credits honest when the designs share
documents.
