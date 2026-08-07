---
status: verified
level: applied
base: scratch
label: When the bidders learn
verified: 2026-08-08
---

# Revenue measured during the transition is not the revenue that settles

**Question:** [stage 28's auction revenue](../) compares payment rules.
This chapter reads the executed transition-measurement audit and asks
when a platform should sample revenue after a rule change, given that
bidders adapt to the rule.

**Before this:** [stage 28 — auction revenue](../) and its executed
first-versus-second-price model and shading-dynamics audit.

## The measurement window, executed

The run ([record](runs/2026-08-08-transition-measurement.md)) runs the
stage's learning dynamics for 20 rounds and reads revenue at six
points after the transition to first price:

| measure at | revenue read | vs second price |
|---:|---:|---:|
| round 1 (day one) | 0.7485 | +49.7% |
| round 2 | 0.6522 | +30.4% |
| round 4 | 0.5585 | +11.7% |
| round 8 | 0.5038 | +0.8% |
| round 14 | 0.4977 | -0.5% |
| round 20 | 0.4766 | -4.7% |

Day-one read overstates settled revenue by 57 percent.

## The failure mode, named

**Revenue is a function of when you measure it.** The day-one read of
0.7485 is the naive market — bidders still bidding truthfully into the
new rule. As they learn to shade, revenue falls toward the equilibrium,
which for this market is the second-price level. A platform that
decides on the early number sees first price worth 50 percent more
than it settles to, and over-invests in a rule change whose advantage
is a transient (Google, 2019-09-04, announced the move to first-price
auctions for Google Ad Manager partners with the expectation that
bidders would adapt their bidding; the settled market is the one the
platform has to live with, not the transition week).

**The platform's own levers are part of the bidders' learning
environment.** The reserve, the floor, and the rule itself are not
exogenous knobs the platform turns while the demand side stays fixed —
they are the game bidders are learning to play (Myerson, 1981,
characterizes the revenue-optimal auction as a reserve-priced
mechanism; Vickrey, 1961, and Edelman, Ostrovsky & Schwarz, 2007, and
Varian, 2007, define the rules bidders shade against). Measuring
revenue without modeling the demand side's response measures a
transient, and the stage's audit is the mechanism: revenue eroded from
0.7485 to 0.4980 as the shading learned.

**The revenue comparison in the stage assumes the bidding behavior.**
The one-shot naive-versus-shaded table in the stage's main path is a
snapshot; the learning dynamics show that both snapshots are real at
different times. The failure mode is treating a point-in-time revenue
read as a property of the rule, when it is a property of the rule
plus the bidders' current adaptation state.

## Who owns the loop

- **The marketplace economics team** owns the revenue read and its
  window: which phase of bidder adaptation a measured number comes
  from, and the settled-state model that predicts where revenue lands.
  It owns the transient-as-property failure — the audit measured a
  day-one read 57 percent above the settled number (Vickrey, 1961;
  Myerson, 1981).
- **The auction engineering team** owns the rule and the reserve:
  the mechanism bidders learn, and the floor the platform sets. It
  owns the endogenous-lever failure — every platform action changes
  the distribution bidders best-respond to (Edelman, Ostrovsky &
  Schwarz, 2007; Varian, 2007).
- **The demand and bidder-facing team** owns the adaptation signal:
  shading estimates per bidder segment, win-margin trends, and how
  fast the market moves toward equilibrium. It owns the
  invisible-transition failure — a market that looks great on day one
  and erodes over weeks is invisible to any report that averages
  across the window.

When the ownership is implicit, the economics team certifies revenue on
the first month after a change, engineering tunes the reserve against a
static demand model, and the platform invests in a rule whose advantage
is 57 percent smaller once bidders learn.

## The fix and its trade

The measured fix is to decide on settled-state revenue, not transition
revenue: run the market long enough (or model the bidders' adaptation)
and read the equilibrium, which for this market is the second-price
level (Google's 2019 first-price transition is the industrial example —
the platform announced the rule, bidders adapted, and the relevant
number is the settled market, not the first weeks). The trade is
decision speed: waiting for the market to settle costs weeks of running
a rule on evidence you do not yet trust, while modeling adaptation
imports assumptions about bidder learning that can be wrong. The
executed table is the cost of the fast path: a day-one read that
overstates the settled revenue by 57 percent is a market-design
decision made on a transient.

## Evidence boundary

The executed audit uses the stage's declared learning dynamics over
20 rounds of 300 auctions (fixed seed). It demonstrates the
measurement-window mechanism; real transition measurement uses
switchback or holdout markets and tracks bidder shading per segment
rather than a declared damping rule.

## Check your mental model

Answer each before opening it.

**1. Why is the day-one revenue read not the rule's revenue?**

<details>
<summary>Answer</summary>

Because bidders have not adapted yet. On day one they bid into the new
rule with their old behavior — the audit reads 0.7485, 50 percent
above second price. As they learn the competition and shade, revenue
falls to the settled state near 0.50. The rule's revenue is the
equilibrium the bidders learn to, not the transition's read.

</details>

**2. What does the platform trade when it decides on the settled
number?**

<details>
<summary>Answer</summary>

Decision speed. Waiting for the market to settle means weeks of running
the rule on evidence it does not yet trust; modeling adaptation imports
assumptions about how bidders learn that can be wrong. The alternative
— deciding on the day-one number — is faster but the audit measures
its cost: a read 57 percent above the settled revenue, which turns a
market-design decision into a bet on a transient.

</details>

## Next

Back to [stage 28](../), where the auction rule is a revenue decision.
The [first-price detour](../when-first-price-pays-more/) shows the
one-shot shading comparison, and the [reserve detour](../when-the-reserve-moves-revenue/)
shows the second lever on the same curve.
