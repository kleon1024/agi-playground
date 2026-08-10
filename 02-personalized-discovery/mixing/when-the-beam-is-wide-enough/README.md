---
status: verified
level: applied
base: scratch
label: When the beam is wide enough
verified: 2026-08-06
---

# A narrow beam finding the optimum is not proof a beam is enough

**Question:** [stage 06's slate search](../) uses beam search against
exhaustive search. This chapter reads the recorded run and asks what the
beam result does and does not prove.

**Before this:** [stage 06's mixing](../) and its recorded slate run.

## The numbers, read

The run ([record](runs/2026-08-06-beam-read.md)) reads the recorded output:

| method | result |
|---|---|
| greedy top-5 | 3 sports items (cap violated) |
| category cap 2 | utility 2.2624 |
| beam widths 1, 2, 3, 9 | all match the exhaustive optimum (2.2624) |
| ad loads 0/1/2 | revenue 0.000/0.872/1.423; displaced value 0.0000/0.7821/1.2659 |

## Two readings

**The beam matched the exhaustive optimum at every width — including width
1.** That is not proof a narrow beam is enough. It says this constructed
catalogue did not expose an approximation loss: the slate's structure is
simple enough that even a greedy prefix search finds the optimum. The
stage's own warning is the right reading — change the seed, category cap,
or catalogue shape before trusting a beam width, because a benchmark where
a heuristic always wins normally forgot to contain the hard case.

**Diversity as a constraint, not a penalty, is what made the beam honest.**
Greedy produced 3 sports items; the cap enforced 2. The cap is a constraint
with an owner — no slate may violate it — while a penalty would let an
unusually valuable duplicate outweigh the diversity loss. The recorded
contrast (cap vs penalty) is the difference between an auditable obligation
and a trade the product owner must accept.

## The fix and its trade

The fix is to build the hard case into the benchmark before trusting a beam
width — a heuristic that always wins is a benchmark that forgot to contain
the approximation loss. The executed read prices the trap: beam widths 1,
2, 3, and 9 all match the exhaustive optimum (2.2624) on the stage's
catalogue, and greedy top-5 produces 3 sports items (cap violated) while
cap=2 restores 2.2624 — the catalogue is simple enough that even a greedy
prefix search finds the optimum, so width-1 success proves nothing about
real slate geometry.

The trade, named: honest benchmarking costs catalogue construction — the
team must vary the seed, category cap, and catalogue shape until the beam
and the exhaustive search disagree, because that is the only way to see
the compute-quality curve the width dial buys. A constraint (cap) and a
penalty are different promises: the cap is an auditable obligation with an
owner, while a penalty lets an unusually valuable duplicate outweigh the
diversity loss — the executed cap-versus-penalty contrast is the difference
between an obligation and a trade the product owner must accept.

## Who owns the loop

- **The mixer team** owns the beam width and the benchmark construction —
  the hard case is their test fixture, not a discovery made in production.
- **The evaluation team** owns the exhaustive-versus-beam comparison per
  catalogue shape, so approximation loss is measured, not assumed absent.
- **The product team** owns the diversity constraint the beam must honor —
  "never more than two sports items" is a promise with an owner.

## Evidence boundary

The recorded slate run (synthetic values, one catalogue, seed 42, trade
rate 3.0 tuned only to reveal displacement). It reads that artifact; it
does not re-run the search and the beam results characterize the synthetic
catalogue, not production slates.

## Check your mental model

Answer each before opening it.

**1. Why is width-1 matching the optimum not evidence that width-1 is
enough?**

<details>
<summary>Answer</summary>

Because the catalogue never exposed a case where a greedy prefix decision
was wrong. Beam search's risk is that the best slate passes through a
prefix that looks bad early; if no item in this catalogue has that shape,
every width finds the optimum. The result is evidence about the catalogue,
not about beam search in general — which is why the stage says to change
the seed and cap before trusting a width.

</details>

**2. What does the displacement column add to the revenue column?**

<details>
<summary>Answer</summary>

It prices the revenue. Revenue 1.423 at ad load 2 looks good until you read
the displaced value beside it (1.2659) — the organic value those ads
pushed out of the slate. The two columns together are the actual trade the
product makes: monetization is not free, and the displacement number is
what makes the cost legible.

</details>

## Next

Back to [stage 06](../), or to
[what a mixing weight actually trades off](../when-the-trade-weight-moves/)
which reads the same stage's weight side.
