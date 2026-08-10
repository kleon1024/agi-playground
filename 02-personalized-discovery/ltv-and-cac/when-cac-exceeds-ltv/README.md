---
status: verified
level: applied
base: scratch
label: When CAC exceeds LTV
verified: 2026-08-07
---

# The user who costs more than they return is a liability at any volume

**Question:** [stage 55's unit economics](../) priced two channels. This
chapter adds the third, and answers: acquisition channels differ in cost
and in the retention of the users they bring — a channel whose users
leave fast is expensive no matter how cheap the install.

**Before this:** [stage 55 — LTV and CAC](../) and its executed unit
economics read.

## The three channels, executed

The run ([record](runs/2026-08-07-cac-exceeds-ltv-read.md)) computes the
five-month lifetime value per user for three channels:

| channel | cac | ltv | ltv/cac | verdict |
|---|---:|---:|---:|---|
| organic search | \$2.00 | \$12.15 | 6.08 | profitable |
| referral | \$3.50 | \$10.70 | 3.06 | profitable |
| paid installs | \$8.00 | \$7.50 | 0.94 | loses money |

## The reading

Referral clears its cost; paid installs do not. The decision is not the
install price — it is the months after it. A channel with LTV below CAC
pays the platform to grow, and volume makes the loss larger. The channel
that looks cheapest at the signup (paid installs at \$8.00 versus
referral at \$3.50 in CAC) is the one that loses money, because its
users' retention does not cover the acquisition.

## The fix and its trade

The fix is to make the ratio the gate: a channel below 1 is capped or
fixed before it is scaled, and the fix lives on the retention side, not
the install price. The executed read prices the verdict — organic
search at \$2.00 CAC returns \$12.15 (6.08), referral at \$3.50 returns
\$10.70 (3.06), and paid installs at \$8.00 returns \$7.50 (0.94) and
loses money. The channel that looks cheapest at signup is the one that
loses, because its users leave before paying back their cost.

The trade is that scaling a below-1 channel is a negative-ROI action —
each extra paid install adds another \$0.50 of loss, so volume makes the
loss larger, and the alternative is to cap a channel that may still be
growing a cohort the window has not fully seen. The gate is only as
honest as the measurement behind it: per-channel retention curves and
revenue per user, measured over the attribution window, are what turn
"cheap install" from an acquisition fact into a liability verdict.

## Who owns the loop

- **The growth and acquisition team** owns the channel-scaling gate and
  caps or fixes a below-1 channel before scaling it.
- **The measurement and analytics team** owns the per-channel retention
  curves and revenue per user that the ratio is computed from.
- **The finance owner** owns the ratio-gate decision and the volume
  arithmetic that makes a below-1 channel a growing liability.

## Evidence boundary

The executed five-month LTV over three declared channels (illustrative,
deterministic). It demonstrates the mechanism; real decisions need the
per-channel retention curves and revenue per user, measured over the
attribution window.

## Check your mental model

Answer each before opening it.

**1. Why is the highest-CAC channel the one that loses money?**

<details>
<summary>Answer</summary>

Because CAC is only half the ledger: paid installs cost \$8.00 and return
\$7.50, while referral costs \$3.50 and returns \$10.70. The difference
is retention — paid-install users leave before paying back their cost.
The channel is expensive in the months after the signup, which is where
the loss actually lives.

</details>

**2. What does "volume makes the loss larger" mean operationally?**

<details>
<summary>Answer</summary>

That scaling the channel is a negative-ROI action: each extra paid
install adds another \$0.50 of loss, so growth through it destroys value
faster. The ratio is the gate — a channel below 1 should be capped or
fixed before it is scaled, because its users are liabilities, not
customers.

</details>

## Next

Back to [stage 55](../). The [retention-flattens
detour](../when-retention-flattens/) shows where the fix lives: the
retention floor that turns a losing channel's users into paying ones.
