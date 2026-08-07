---
status: verified
level: applied
base: scratch
label: When personalization scares
verified: 2026-08-07
---

# A confident prior reads as a misread

**Question:** [stage 51's first page](../) is a default decision. This
chapter asks what an onboarding prior does to that page, and answers: a
strong prior narrows the slate before the user has shown anything, and a
page that narrows on a single signup click reads as a misread.

**Before this:** [stage 51 — new-user experience](../) and its executed
runway read.

## The narrowing, executed

The run ([record](runs/2026-08-07-personalization-scares-read.md))
measures the chosen category's share of the first page:

| prior strength | categories shown | prior category share |
|---|---:|---:|
| none (0.000) | 3 | 20% |
| weak (0.006) | 3 | 30% |
| strong (0.020) | 3 | 40% |

## The reading

The onboarding boost concentrates the page on the category the user
clicked once at signup — from a fifth of the page with no prior to
two-fifths with a strong one. The more the boost owns, the less of the
catalogue the user sees before proving they want it. A page that narrows
on a single signup click reads as a misread, and the user never comes
back to correct it — the retention cost of the confident prior is paid
before the user has a chance to disagree.

## Evidence boundary

The executed mix over three declared prior strengths (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
the onboarding prior's accuracy and the retention cost of a narrowed
first page, and set the boost strength against both.

## Check your mental model

Answer each before opening it.

**1. Why does a stronger prior show fewer categories?**

<details>
<summary>Answer</summary>

Because the boost inflates the chosen category's score until it dominates
the top slots: at strength 0.020 the category holds 40% of the page,
leaving less room for anything the user did not click once. The
categories shown stay at 3, but the balance moves — the page is no longer
a sample of the catalogue, it is a bet on one click.

</details>

**2. Why is the misread so costly for a new user?**

<details>
<summary>Answer</summary>

Because the user has no relationship with the platform yet: a first page
that looks like a misread reads as "this is not for me", and the user
never produces the interactions that would correct it. Unlike an existing
user, a new user has no reason to stay and disprove the prior — the
misread is the last page they see.

</details>

## Next

Back to [stage 51](../). The [user-is-new
detour](../when-the-user-is-new/) is the same lever measured by outcome:
the prior's NDCG when it is right versus when it is wrong.
