---
status: verified
level: applied
base: scratch
label: When the bandit explores
verified: 2026-08-07
---

# Exploration is a price paid during the runway

**Question:** [stage 51's first page](../) is decided before
personalization can see the user. This chapter asks whether exploration
is the free fix, and answers: on the new-user runway every exploration
round is a round of worse relevance, and the run measures the tax per
exploration budget — greedy from a popularity-initialized estimate pays
nothing, a fixed 10% budget costs measurable relevance, and 30% costs
more.

**Before this:** [stage 51 — new-user experience](../) for the runway
the exploration must bridge, and the [onboarding-prior
detour](../when-the-user-is-new/) for the other lever that moves the
first page.

## The tax, executed

The run ([record](runs/2026-08-07-bandit-explores-read.md)) plays each
policy for the same 20-round runway and averages NDCG@10 across it:

| policy | round 1 | round 5 | round 20 | runway avg |
|---|---:|---:|---:|---:|
| popularity | 0.122 | 0.122 | 0.122 | 0.122 |
| greedy | 0.122 | 0.878 | 0.878 | 0.817 |
| epsilon 10% | 0.122 | 0.878 | 0.878 | 0.795 |
| epsilon 30% | 0.122 | 0.878 | 0.878 | 0.728 |
| Thompson | 0.122 | 0.694 | 0.878 | 0.731 |

## The reading

Everyone who learns ends at the same 0.878 — the difference is what the
runway cost to get there. Greedy from a popularity-initialized estimate
explores implicitly through its ties and pays nothing; a fixed 10%
exploration budget costs 0.022 of runway average, 30% costs 0.090.
Thompson prices exploration by posterior uncertainty instead of a fixed
share, but it still pays 0.087 on a runway this short, because every
round spent on an unproven category is a round the user's first page
paid for.

The production tell is a new-user cohort whose early-session relevance
trails the same cohort a week later: the cohort is paying the
exploration tax. The fix is not "explore more" — it is choosing where
the tax is paid: warm priors and shared user segments move the first
page more than an exploration budget does, and a budget is only worth
its cost when the horizon is long enough to repay it (Thompson, 1933,
for the posterior-sampling original; the bandit's regret accounting is
the standard measure of the tax).

## Evidence boundary

The executed policy comparison over one declared 20-round runway
(illustrative, deterministic, seeded per policy). It demonstrates the
mechanism; real systems must measure their own runway length, the
retention value of early-session relevance, and the prior's accuracy
before choosing an exploration budget, because the tax scales with how
short the horizon is.

## Check your mental model

Answer each before opening it.

**1. Why does greedy "explore implicitly" without an explicit budget?**

<details>
<summary>Answer</summary>

Because the estimate starts at the popularity prior, and while the
estimates are tied the ranking falls back to the prior — so early rounds
are served by popularity, the click feedback differentiates the
categories, and the policy pivots when the evidence outweighs the
default. There is no exploration parameter, yet the first round is
necessarily a popularity round; that fallback is the implicit
exploration, and it is free because it is what the platform would have
served anyway.

</details>

**2. Why is Thompson still 0.731, not 0.878, when it learns at the
same rate?**

<details>
<summary>Answer</summary>

Because the runway average counts every round, including the early ones
where the posterior is broad and Thompson samples categories the user
does not like. It spends exploration where uncertainty is highest — a
principled rule — but on a 20-round horizon those early exploratory
rounds are a large share of the average. The policy's regret is smaller
than epsilon's for the same budget, but it is not zero: exploration is a
tax on a short horizon, not a free discovery service.

</details>

## Next

Back to [stage 51](../). The prior and the exploration budget are the
two levers for the first page; [stage 52 — trust and
explainability](../../52-trust-and-explainability/) asks what the user
must be able to verify about the page those levers produced.
