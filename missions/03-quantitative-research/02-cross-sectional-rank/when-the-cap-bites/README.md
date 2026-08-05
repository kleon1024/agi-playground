---
status: verified
level: applied
base: none
label: When the cap bites
verified: 2026-08-06
---

# What does the position cap actually cost?

**Question:** [stage 02](../) caps every position at a fraction of the book,
and its recorded run measures the rules at one cap. The cap is a dial, not
a setting — this chapter turns it across five values and reads the
three-way trade it makes: concentration, turnover, and the paper return.

**Before this:** [stage 02's sizing rules](../), including its constraint
pipeline.

## The dial, measured

The sweep ([run record](runs/2026-08-06-cap-sweep.md)) fetches the universe
once and runs two sizing rules across caps 0.05 to 1.0:

| cap | gross | HHI (concentration) | turnover/mo | paper Sharpe | cap violations |
|---:|---:|---:|---:|---:|---:|
| 0.05 | 0.79 | 0.032 | 0.206 | -0.76 | 102 |
| 0.10 | 1.34 | 0.090 | 0.289 | -0.65 | 49 |
| 0.25 | 1.45 | 0.109 | 0.303 | -0.66 | 0 |
| 0.50 | 1.45 | 0.109 | 0.303 | -0.66 | 0 |

(rank-proportional rule; the signal-proportional rows follow the same shape)

## Three readings

**The cap binds only below 0.25.** Past it, every row is identical, because
no name's natural weight on this 30-name universe exceeds 25% of the book. A
cap that never binds is a policy that does nothing; the sweep shows where
this one starts to act.

**The cap trades exposure for diversification, not for return.** Tighter
caps cut concentration (HHI 0.109 to 0.032) and shrink gross exposure (1.45
to 0.79) — the book owns less market — and on this window the paper Sharpe
does not improve (-0.66 to -0.76 for rank). Diversification is a risk
property, not a return property, and the sweep separates the two: the cap
bought the former and paid with the latter.

**The violation count is a tightness tax.** Sector demeaning can push a name
that was exactly at the cap back over it — the stage's own constraint
pipeline artifact — and the count scales with tightness: 102 re-breaches at
0.05, 49 at 0.10, zero at 0.25+. A tighter cap does not just restrict; it
interacts with the next constraint in the pipeline, and the interaction is
measurable.

## Evidence boundary

One fetch window (live endpoint, drifts between runs), one momentum signal,
two sizing rules, thirty names. The Sharpe signs are this window's regime
and carry no claim beyond it; the cap's shape — binds below ~0.25, trades
exposure for diversification, taxes tightness — is the durable finding, not
the sign of the return.

## Check your mental model

Answer each before opening it.

**1. Why are the 0.50 and 1.00 rows identical to 0.25?**

<details>
<summary>Answer</summary>

Because the cap stops binding: on this 30-name universe no name's natural
weight ever exceeds 25% of the book, so a cap of 0.25 or looser never clips
anything. The identical rows are the measurement that the policy is inert
there — a cap is only a policy where it actually clips.

</details>

**2. The cap cuts concentration but not the Sharpe. What does that
combination establish about the cap's purpose?**

<details>
<summary>Answer</summary>

That the cap is a risk-control, not a return-improver. It forces the book to
own less of any single name — lower HHI, lower gross — and on this window
that did not make the paper return better. A cap justified as "it will
improve performance" is making the wrong promise; its honest justification
is a constraint on what the book can become, which is a different claim.

</details>

## Next

[Stage 03's walk-forward](../../03-walk-forward-validation/): the cap's
concentration and turnover trade is consumed there, where the paper book
has to survive its own trading bill.
