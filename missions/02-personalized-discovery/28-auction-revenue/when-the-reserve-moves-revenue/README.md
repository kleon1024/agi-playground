---
status: verified
level: applied
base: scratch
label: When the reserve moves revenue
verified: 2026-08-07
---

# The reserve sits on the demand curve

**Question:** [stage 28's auction revenue](../) compared payment rules.
This chapter reads the executed reserve sweep and asks where the
revenue-maximizing reserve lives.

**Before this:** [stage 28 — auction revenue](../) and its executed
first-versus-second-price model.

## The sweep, executed

The run ([record](runs/2026-08-07-reserve-revenue-read.md)) sweeps the
reserve and reads fill and expected revenue:

| reserve | fill | expected revenue |
|---|---:|---:|
| \$0.0 | 1.00 | \$0.00 |
| \$0.5 | 0.67 | \$0.33 |
| \$0.8 | 0.47 | \$0.37 |
| \$1.0 | 0.33 | \$0.33 |
| \$1.2 | 0.20 | \$0.24 |

## The reading

A zero reserve fills every slot at zero price; a high reserve prices
each sale high but sells few. The revenue-maximizing reserve sits
between the two — here at \$0.8, where expected revenue peaks at \$0.37
before fill collapses. The optimum is a property of the demand curve:
it is the point where price per sale and probability of sale balance,
which is why it is estimated from bid data, not guessed.

## Evidence boundary

The executed sweep over a declared demand distribution (illustrative,
deterministic). It demonstrates the shape; real reserve optimization
estimates the demand curve from bid history and re-optimizes as the
curve moves.

## Check your mental model

Answer each before opening it.

**1. Why is zero reserve not the revenue-maximizing choice?**

<details>
<summary>Answer</summary>

Because it sells every slot at zero price — the auction's payment rule
only pays when there is a second bidder, and with no reserve a
single-bidder slot earns nothing. The reserve is the floor that turns
empty competition into revenue, which is the one-bidder case stage 14
ended on.

</details>

**2. Why does revenue fall after the peak?**

<details>
<summary>Answer</summary>

Because the higher reserve prices more auctions out. Above \$0.8, fill
collapses faster than price rises — at \$1.2 only 20% of auctions sell,
and expected revenue drops to \$0.24. The optimum is the point where
the two curves balance, which depends on the demand distribution, not
on the rule.

</details>

## Next

Back to [stage 28](../), where the auction rule is a revenue decision.
The [shading detour](../when-first-price-pays-more/) shows the bidder
behavior side of the same equation.
