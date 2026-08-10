---
status: verified
level: applied
base: scratch
label: When retention flattens
verified: 2026-08-07
---

# The user who stops leaving is worth more than the user who stops coming

**Question:** [stage 55's unit economics](../) priced the channels. This
chapter asks where LTV actually comes from, and answers: two cohorts can
retain the same share in month one and diverge completely — the cohort
that flattens at a floor keeps compounding, which is where the
recommendation system earns its keep.

**Before this:** [stage 55 — LTV and CAC](../) and its executed unit
economics read.

## The two cohorts, executed

The run ([record](runs/2026-08-07-retention-flattens-read.md)) projects
24-month LTV for a decaying cohort and a flattening one:

| cohort | month-12 retention | ltv |
|---|---:|---:|
| decaying (floor 0) | 1% | \$27.54 |
| flattening (floor 35%) | 35% | \$50.83 |

## The reading

Both cohorts decay at the same rate for months; the floor decides the
difference. A 35% floor nearly doubles LTV because the flat tail
compounds over the horizon. Retention work — which is what good discovery
is — changes the floor, and the floor is worth more than any single
month's revenue: keeping an existing user from leaving adds the whole
future stream, while acquiring a new one (stage 55's CAC) pays the
acquisition cost first.

## The fix and its trade

The fix is to measure the retention floor per cohort and treat discovery
as a floor lever: LTV is priced on the floor, and retention work — which
is what good discovery is — changes it. The executed projection prices
the difference: both cohorts decay at the same rate for months, yet the
decaying cohort (floor 0) holds 1 percent at month 12 and is worth
\$27.54, while the flattening cohort (floor 35 percent) holds 35 percent
and is worth \$50.83 — the floor nearly doubles LTV because the flat
tail compounds over the whole horizon.

The trade is that the floor is worth more than any single month's
revenue, and the work that raises it is slower to measure than an
acquisition campaign: keeping an existing user from leaving adds the
whole future stream, while acquiring a new one pays the acquisition cost
first. A discovery improvement that shifts the floor is therefore worth
more than the same effort spent on new users, but only if the floor is
validated on live cohorts — the projection is a mechanism demo until the
real retention curve confirms it.

## Who owns the loop

- **The discovery and ranking team** owns the floor lever, the retention
  work that keeps users compounding.
- **The measurement team** owns the per-cohort retention curves and the
  live-cohort validation of the floor.
- **The growth and finance owner** owns the LTV pricing that puts a
  dollar value on a floor point, the number that prioritizes retention
  against acquisition spend.

## Evidence boundary

The executed 24-month projection over declared retention curves
(illustrative, deterministic). It demonstrates the mechanism; real LTV
needs the measured retention curve per cohort and the revenue per
retained user, and the floor itself must be validated on live cohorts.

## Check your mental model

Answer each before opening it.

**1. Why does a 35% floor nearly double the LTV?**

<details>
<summary>Answer</summary>

Because LTV is a sum over the horizon: the decaying cohort's users are
nearly all gone by month 12 (1% retained), so few months of revenue
remain; the flattening cohort still holds 35% at month 12, so its revenue
keeps accumulating month after month. The floor is not a single month's
boost — it is a multiplier over every future month.

</details>

**2. How is discovery a retention lever?**

<details>
<summary>Answer</summary>

Because users stay when the platform keeps returning value: the mission's
own goal — reducing the time to find something worth attention — is
exactly what raises the retention floor. The flattening-cohort read puts
a price on that work: each point of floor compounds into LTV, and a
discovery improvement that shifts the floor is worth more than the same
effort spent acquiring new users.

</details>

## Next

Back to [stage 55](../) and the [mission README](../../../) — the operations
track closes the discovery loop with the economics that decide whether
the whole mission's value is real. The [CAC-exceeds-LTV
detour](../when-cac-exceeds-ltv/) is the other half: the acquisition
side, where a channel's users leave before paying back their cost.
