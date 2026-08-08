---
status: verified
level: applied
base: scratch
label: When first price pays more
verified: 2026-08-07
---

# First price pays more only when bidders stay honest

**Question:** [stage 28's auction revenue](../) compared payment rules.
This chapter reads the executed shading comparison and asks whether
first price's revenue edge survives bidder behavior.

**Before this:** [stage 28 — auction revenue](../) and its executed
first-versus-second-price model.

## The comparison, executed

The run ([record](runs/2026-08-07-first-price-read.md)) runs the same
auction under naive and shaded bidders:

| bidders | first price | second price | gap |
|---|---:|---:|---:|
| naive | \$1.20 | \$1.00 | \$0.20 |
| shaded | \$0.96 | \$0.80 | \$0.16 |

## The reading

First price pays more when bidders bid truthfully and less when they
shade. The revenue rule and the bidder population are coupled — a
revenue comparison is only valid for the bidding behavior it assumes.
The naive case is the upper bound; as soon as bidders learn the rule
and shade toward it, the gap narrows. Stage 14's honest-bidding
property is the reason second price exists: it makes the bid the value,
so the platform's revenue and the auction's efficiency are not hostage
to how bidders game the payment rule.

## The fix and its trade

The measured fix is to price the rule with the bidder population, not
without it: model the shading (or measure it from bid data) and compare
revenue at the shaded equilibrium, where the first-price gap narrows to
\$0.16 — and remember the equilibrium itself is a moving target, since
the stage's audit shows revenue eroding from 0.7485 to 0.4980 as
bidders learn (Vickrey, 1961, revenue equivalence; Edelman, Ostrovsky
& Schwarz, 2007, and Varian, 2007, for the mechanisms bidders adapt
to). The trade is between the rules themselves: second price removes
the shading incentive entirely — truthful bidding makes the bid the
value, so revenue is stable across bidder behavior — while first price
keeps the higher naive ceiling but requires the platform to model and
counter bidder learning, which the audit shows is a losing race
(Google's 2019 first-price transition is the industrial version: the
advantage was the transition's, not the settlement's).

## Who owns the loop

- **The marketplace economics team** owns the revenue read with the
  bidder population: a first-price comparison is only valid for the
  shading behavior it assumes.
- **The auction engineering team** owns the rule choice — second price's
  truthful-bidding stability versus first price's higher naive ceiling
  — and the transition's settlement.
- **The demand and bidder-facing team** owns the shading estimates and
  their evolution, the input that decides which revenue number is real.

## Evidence boundary

The executed comparison over one bid set and two declared behaviors
(illustrative, deterministic). It demonstrates the coupling; real
revenue comparisons require the bidder population's shading model,
which is itself estimated from bid data.

## Check your mental model

Answer each before opening it.

**1. Why does shading shrink the first-price gap?**

<details>
<summary>Answer</summary>

Because first price charges the winner its own bid, so rational bidders
bid below value to leave room. Shading lowers the winning bid, and the
platform's revenue falls with it — the gap drops from \$0.20 to \$0.16.
The rule's revenue depends on how well bidders can predict the auction.

</details>

**2. What does second price buy that first price cannot?**

<details>
<summary>Answer</summary>

Truthful bidding. Under second price the winner pays the second bid, so
bidding value is dominant and shading is unnecessary — the bid reveals
value, which stage 14 established. First price has to model and counter
bidder shading; second price removes the incentive, which is why its
revenue comparison is stable across bidder behavior.

</details>

## Next

Back to [stage 28](../), where the auction rule is a revenue decision.
The [reserve detour](../when-the-reserve-moves-revenue/) shows the
second lever on the same curve.
