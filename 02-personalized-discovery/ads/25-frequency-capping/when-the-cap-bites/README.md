---
status: verified
level: applied
base: scratch
label: When the cap bites
verified: 2026-08-07
---

# The cap is a budget allocation, not a setting

**Question:** [stage 25's frequency capping](../) limits exposures per
user. This chapter reads the executed reach allocation and asks what a
higher cap actually costs.

**Before this:** [stage 25 — frequency capping](../) and its executed
CTR-decay model.

## The allocation, executed

The run ([record](runs/2026-08-07-cap-bites-read.md)) allocates a
10,000-impression budget across cap levels:

| cap | users reached | impressions each |
|---:|---:|---:|
| 1 | 10,000 | 1 |
| 3 | 3,333 | 3 |
| 5 | 2,000 | 5 |
| 10 | 1,000 | 10 |

## The reading

The same budget reaches 10,000 users at cap 1 and only 1,000 at cap 10.
A high cap preserves per-user value — more of the user's exposures land
in the high-CTR early range — but shrinks reach. The campaign's goal
decides which side of the trade it needs: a brand seeking reach wants a
low cap, a performance campaign seeking frequency wants a higher one.
The cap is a budget allocation, not a display setting.

## The fix and its trade

The measured fix is to set the cap from the campaign's objective and
the measured fatigue curve, not from a default: reach goals want the
cap low (10,000 users at cap 1), frequency goals want it higher (1,000
users at cap 10), and the curve says how much each extra impression is
worth. The production alternative to a hard cut is soft capping — serve
past the cap with a probability that decays with exposure instead of a
sharp stop — which blurs the reach-frequency cliff rather than
abolishing it: Aharon et al. (2023, arXiv:2312.05052) showed soft
frequency capping in Yahoo Gemini Native lifted revenue 7.3 percent in
a bucket test. The trade is on the cliff itself: a hard cap guarantees
the fatigue control but collapses reach (10x fewer users from cap 1 to
cap 10), while soft capping preserves reach at the price of serving
some impressions past the useful exposure range — the exact waste the
[fatigue detour](../when-fatigue-hits/) prices.

## Evidence boundary

The executed allocation over a declared impression budget (illustrative,
deterministic, uniform delivery). It demonstrates the arithmetic; real
reach also depends on the available user pool and the delivery
schedule, which stage 17's pacing owns.

## Check your mental model

Answer each before opening it.

**1. Why does a higher cap reach fewer users?**

<details>
<summary>Answer</summary>

Because the impression budget is fixed and a cap decides how many
impressions each user can consume. Cap 10 lets 1,000 users absorb all
10,000 impressions; cap 1 spreads them across 10,000 users. The cap is
the allocation rule between depth and breadth.

</details>

**2. What decides where on the trade a campaign should sit?**

<details>
<summary>Answer</summary>

The campaign's objective. Reach goals (new users, awareness) want more
users at fewer impressions each; frequency goals (reinforcement,
performance) want depth on a smaller set. The cap states which the
budget serves, and the CTR-decay curve says how much each extra
impression is worth.

</details>

## Next

Back to [stage 25](../), where the cap is a value decision. The
[fatigue detour](../when-fatigue-hits/) prices what the cap saves.
