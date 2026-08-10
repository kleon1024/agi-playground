---
status: verified
level: applied
base: scratch
label: When the user is new
verified: 2026-08-07
---

# The onboarding prior is a bet on an answer the user may not mean

**Question:** [stage 51's first page](../) is a default decision. This
chapter asks whether asking the new user works, and answers: a right
prior lifts the first page above popularity, a wrong one sinks it below —
the bet is on the asking and the honesty of the answer.

**Before this:** [stage 51 — new-user experience](../) and its executed
runway read.

## The bet, executed

The run ([record](runs/2026-08-07-user-is-new-read.md)) serves the first
page under different priors:

| prior | first-page ndcg@10 |
|---|---:|
| popularity only | 0.122 |
| onboarding prior on [2, 3] | 0.878 |
| onboarding prior on [0, 4] | 0.000 |

## The reading

The right prior lifts the first page from 0.122 to 0.878; the wrong one
collapses it to 0.000. Onboarding is a high-leverage bet — it decides the
first page for a user with no trail, and it is wrong whenever users do
not say what they mean or the option set misleads them. The prior is not
free knowledge; it is a claim about the user that the platform cannot yet
verify, and the cost of a wrong claim is a first page that matches
nothing the user wants.

## The fix and its trade

The fix is to treat the onboarding prior as a falsifiable claim: measure
its accuracy on the real signup flow and pair it with reserved
exploration slots that can disprove it, so a wrong claim is caught
before it owns the first page. The executed bet prices the stakes — the
right prior lifts first-page NDCG@10 from popularity's 0.122 to 0.878,
and the wrong prior collapses it to 0.000, because every slot is filled
by the mistaken category and the user's true interests are ranked out
entirely.

The trade is that the asking itself is a risk: users do not always say
what they mean, and the option set shapes the answer, so the bet is on
both the user's honesty and the design of the ask. A confident wrong
prior is worse than no prior — popularity at least matches some users
some of the time — and the hedge is exploration, which costs relevance
on the short runway but is the only mechanism that catches the wrong
claim. The onboarding team owns the ask, the ranking team owns the
reserved slots, and the measurement team owns the accuracy number the
bet is priced on.

## Who owns the loop

- **The growth and onboarding team** owns the signup ask and the prior
  it produces, including the option set that shapes the answer.
- **The ranking team** owns the reserved exploration slots that can
  disprove the claim before it owns the whole page.
- **The measurement team** owns the prior-accuracy measurement on the
  live flow, the number that says whether the bet is paying.

## Evidence boundary

The executed NDCG comparison over declared priors (illustrative,
deterministic). It demonstrates the mechanism; real systems must measure
the prior's accuracy on their own signup flow, and pair it with
exploration so the platform can discover when the claim is wrong.

## Check your mental model

Answer each before opening it.

**1. Why does the wrong prior score 0.000 instead of just below
popularity?**

<details>
<summary>Answer</summary>

Because the prior does not merely fail to help — it actively ranks the
user's true interests out of the page. Every slot is filled by the
mistaken category, so NDCG@10 sees zero relevant items in the top ten.
A wrong prior is worse than no prior: popularity at least matches some
users some of the time, while a confident wrong bet matches no one.

</details>

**2. What makes the asking itself a risk?**

<details>
<summary>Answer</summary>

Users do not always say what they mean, and the option set shapes the
answer: a category picked fast at signup is a weak signal, and the prior
treats it as truth. The bet is therefore on both the user's honesty and
the design of the ask. Exploration is the hedge — serving the prior while
reserving slots that can disprove it, so a wrong claim is caught before
it owns the whole first page.

</details>

## Next

Back to [stage 51](../). The [personalization-scares
detour](../when-personalization-scares/) is the same lever read from the
page itself: how much of the first page the prior is allowed to own.
