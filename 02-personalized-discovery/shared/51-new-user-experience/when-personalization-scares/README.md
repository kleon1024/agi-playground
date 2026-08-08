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

## The fix and its trade

The fix is to let the prior own a bounded share of the first page, with
the boost strength set against the prior's measured accuracy and the
retention cost of the narrowed page. The executed mix prices the choice
— no prior leaves the clicked category at a fifth of the page, a weak
prior (0.006) raises it to 30 percent, and a strong one (0.020) to 40
percent, with the category count unchanged at 3 the whole time. The
boost does not add categories; it shifts the balance until the page is a
bet on one click rather than a sample of the catalogue.

The trade is that the stronger the prior, the less of the catalogue the
user sees before proving they want it — and the new user has no
relationship to correct a misread with, so a page that narrows on a
single signup click reads as "this is not for me" and the retention cost
is paid before the user can disagree. The measurement team reports the
prior's accuracy and the narrowed-page retention cost together, because
the strength decision needs both numbers on the same page.

## Who owns the loop

- **The growth and onboarding team** owns the signup ask and the prior
  it produces, the claim the first page is built on.
- **The ranking team** owns the boost strength on the slate and the
  share of the page the prior may hold.
- **The measurement team** owns the prior-accuracy and retention-cost
  numbers the strength decision is priced on.

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
