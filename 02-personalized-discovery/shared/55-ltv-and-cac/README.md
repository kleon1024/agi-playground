---
status: verified
level: applied
base: scratch
label: LTV and CAC
verified: 2026-08-07
---

# A user is worth what they keep returning and spending

**Question:** stage 54 followed the advertiser's return. This stage asks
the same question for the platform's own users, and answers: lifetime
value is retention times revenue per retained user, acquisition cost is
what a channel charges for a signup, and the ratio decides which channels
the platform can afford to buy users from at all.

**Before this:** [stage 30 — ads measurement](../../ads/30-ads-measurement/) for
the attribution these numbers depend on, and [stage 54 — advertiser
ROAS](../../ads/56-advertiser-roas/) for the advertiser-side economics this
completes.

## The unit economics, executed

The run ([record](runs/2026-08-07-ltv-and-cac.md)) computes the five-month
lifetime value per user for two channels:

| channel | cac | ltv | ltv/cac |
|---|---:|---:|---:|
| organic search | \$2.00 | \$12.15 | 6.08 |
| paid installs | \$8.00 | \$7.50 | 0.94 |
| referral | \$4.00 | \$7.20 | 1.80 |

<!-- interactive: LtvCac -->

## The mechanism, named

Organic search pays back about six times its acquisition cost; paid
installs return less than the cost of the user — every paid signup loses
money once retention is counted. A channel with a low CAC is not a cheap
channel if its users leave. Lifetime value is retention times revenue per
retained user summed over the horizon, and acquisition cost is what the
channel charges; unit economics decide which growth is real growth.

## How you find it: the measured window, executed

LTV/CAC is a curve over the horizon, not a number. The run
([record](runs/2026-08-07-ltv-and-cac.md)) emits each channel's full
24-month retention curve, and the audit
([record](runs/2026-08-07-unit-economics-audit.md) —
[`prod/unit_economics_audit.py`](prod/unit_economics_audit.py))
recomputes LTV/CAC per measured window, the way a growth finance team
re-measures unit economics before scaling an acquisition bet:

| channel | 1m | 3m | 6m | 12m | 24m |
|---|---:|---:|---:|---:|---:|
| organic search | 2.50 | 4.58 | 6.67 | 8.77 | 9.86 |
| paid installs | 0.62 | 0.88 | 0.95 | 0.97 | 0.97 |
| referral | 0.12 | 0.78 | 2.31 | 5.20 | 10.02 |

The verdict is WINDOW TRUNCATED: at 3 months organic search tops the
ranking and paid installs sits above referral (0.88 vs 0.78); at 24
months referral tops it (10.02) while paid installs never improves. The
window you measured decides which channel you call the acquisition bet —
channels that ramp slowly and stay are understated at short windows, so
re-measure LTV on the full retention curve, modeled from the cohort's
own recency-frequency data (BG/NBD-style; Fader, Hardie & Lee,
"Counting Your Customers the Easy Way", Marketing Science 2005;
customer valuation in Gupta, Lehmann & Stuart, "Valuing Customers",
Journal of Marketing Research 2004), before scaling spend.

## The fix and its trade

The fix is to re-measure LTV on the full retention curve — modeled from
the cohort's own recency-frequency data (BG/NBD-style), not from the
window that happens to have elapsed — and to report the ratio per
horizon before scaling an acquisition bet. The audit prices the repair:
at 3 months organic search tops the ranking (4.58) and paid installs
sits above referral (0.88 vs 0.78), while at 24 months referral tops it
(10.02) and organic reaches 9.86, with paid installs flat at 0.97
throughout — the window you measured decides which channel you call the
acquisition bet, so the curve, not the snapshot, is the verdict.

The trade is that the curve costs data, and every input to the ratio
drifts. Modeling the full retention curve needs per-cohort retention
and revenue-per-user data over the horizon, which is exactly the
measurement the fast-decay channel's numbers are built to avoid
reporting; CAC and retention both shift after a launch, so the model
needs a re-measurement cadence. The consequence of skipping the curve
is the detour's read: a team that trusts the 3-month window keeps
funding the channel that decays (paid installs, 0.94 at five months)
and starves the one that ramps and stays (referral, clearing its cost
at 3.06 and reaching 11.78 at 24 months) — the wrong acquisition bet
scales on a snapshot.

## Who owns the loop

The unit economics only stay honest if someone owns each side of the
ledger, and the handoffs are where the stage's failure modes live:

- **The growth finance team** owns the LTV model: the horizon, the
  retention curve's shape, and the recency-frequency fit that keeps a
  truncated window from deciding a channel verdict. It owns the
  numerator.
- **The acquisition team** owns CAC per channel and the spend decision:
  which channels scale, and the cost per signup each one actually
  charges. It owns the denominator, and the when-cac-exceeds-ltv detour
  shows the failure when the ratio crosses below one.
- **The analytics team** owns cohort retention measurement: the per-
  cohort curves that feed the LTV model, and the re-measurement cadence
  that catches curves drifting after a launch. It owns the data the
  finance team's verdict is built on.

When the ownership is implicit, each side optimizes its own number: the
acquisition team buys the cheapest signups, the analytics team reports
windowed retention, and nobody owns the curve — so the slowly-ramping
channel stays underfunded, the fast-decay channel keeps its budget, and
the platform's "growth" is a ledger of users who never pay back.

## Why this belongs in the mission

The mission ends where the platform's health is decided: a discovery
system that improves retention changes LTV, and LTV is what makes every
acquisition channel affordable. The ads track priced impressions; this
stage prices users, closing the loop the mission opened with "reduce the
time to find something worth attention" — because time saved is retention
earned, and retention is the multiplier in the unit economics.

## Evidence boundary

The executed five-month LTV over declared retention and revenue
(illustrative, deterministic). It demonstrates the mechanism; real unit
economics need the measured retention curve per cohort, real revenue per
user, the attribution window, and channel CACs — all of which shift and
must be re-measured.

## Check your mental model

Answer each before opening it.

**1. Why does paid installs lose money despite paying for signups?**

<details>
<summary>Answer</summary>

Because the signup is only the start of the ledger: paid installs cost
\$8.00 and return \$7.50 over five months — the user's revenue does not
cover the acquisition. The channel is not cheap at the install; it is
expensive in the retention, because its users leave before paying back
their cost.

</details>

**2. What does an LTV/CAC ratio below 1 mean for growth?**

<details>
<summary>Answer</summary>

That every user bought through the channel is a loss: scaling the channel
scales the loss, so "growth" through it is actually shrinking the
company. The ratio is the gate that separates real growth — channels
where LTV clears CAC — from vanity volume, and it is why the retention
work (the flattening-cohort detour) is worth more than any single
acquisition push.

</details>

**3. Why does the 3-month window rank paid installs above referral when
referral is worth more overall?**

<details>
<summary>Answer</summary>

Because paid installs' curve is fully visible at three months — it decays
from month one — while referral's users are still ramping: at 3 months
referral's LTV/CAC is 0.78, at 24 months it is 10.02, and paid installs
stays flat at 0.97 throughout. A windowed number is a snapshot of a
curve, so a short window systematically understates channels whose value
arrives late. The horizon is a modeling choice, and it flips the verdict;
report the ratio per horizon and model the curve before scaling spend.

</details>

## Next

The unit economics close the mission's loop: retention is what discovery
earns. A detour from here: [the user who costs more than they return is
a liability at any volume](when-cac-exceeds-ltv/) — the executed read:
referral clears its cost at 3.06, paid installs lose money at 0.94.

Another detour: [the user who stops leaving is worth more than the user
who stops coming](when-retention-flattens/) — the executed read: a 35%
retention floor nearly doubles 24-month LTV from \$27.54 to \$50.83.

A third detour: [the observed window decides the channel
verdict](when-the-retention-window-truncates/) — the executed read: paid
installs looks like the better bet at 3 months (0.88 vs 0.78), and
referral is 11.78 against paid's 0.97 at 24 months, so a team that reads
the window and stops ranks the wrong channel.
