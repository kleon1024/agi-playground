---
status: verified
level: applied
base: scratch
label: When the blend biases the credit
verified: 2026-08-08
---

# The blend, not the ranking, can hand the win to one team

**Question:** [stage 38's interleaving](../) credits clicks to the
team that proposed each clicked result. This chapter reads the
executed blend-variance audit and asks who actually won the experiment
when the two teams are equal.

**Before this:** [stage 38 — interleaving experiments](../) and its
executed interleave-position audit, and [stage 30 — ads
measurement](../../30-ads-measurement/) for the increment-discipline
interleaving replaces.

## The blend, executed

The run ([record](runs/2026-08-08-blend-variance.md)) simulates 2,000
experiments of 3,000 sessions each, with equal teams and disjoint
proposals, under two blending policies:

| policy | credited share, team A | spread across experiments |
|---|---:|---|
| naive (team A starts every session) | 59.3% | SD 0.99%, interval 57.4-61.3% |
| balanced (random start per session) | 50.0% | SD 1.00%, interval 48.1-52.0% |

The naive blend's interval does not even touch 50 percent, and the
teams are equal — the credited win belongs to the blend, not the
ranking.

## The failure mode, named and audited

**The naive blend's answer is confidently wrong.** The audit's
position click model gives team A's slots click mass 0.51 and team B's
0.35, so the naive blend credits A with 59.3 percent of clicked
sessions. The failure is not noise: at 200,000 sessions the interval is
+/-0.23 percent around 59.3 percent, and the true 50/50 is 78 standard
errors away. More traffic does not fix a fixed bias — it pins the wrong
center down more tightly. The balanced policy randomizes the start,
averaging the two lists, and lands at 50.0 percent. Position bias is
the mechanism: users click whatever sits near the top regardless of
quality (Joachims et al., 2005, SIGIR), and a blend that hands one team
the better slots credits clicks that team did not earn (Chapelle et
al., 2012, TOIS; Radlinski & Craswell, 2010, SIGIR).

**The fix is the random start, and the trade is small.** The same run
measures the cost instead of asserting it: the start flip raises the
per-session outcome variance from 0.2413 to 0.2500, exactly 3.6
percent, so the balanced design needs 3.6 percent more sessions for the
same confidence-interval width — and the empirical spread matches
(0.99 percent vs 1.00 percent). The bias is the dominant failure, and
removing it is nearly free. What the balanced design does cost in
production is the discipline of a declared randomization: the start
decision must be per-session random, pre-registered, and analyzed as
one pooled comparison — a team that randomizes but then reads the two
list variants as separate experiments halves its effective sample.

## The fix and its trade

The fix is to randomize which team starts each session, so the two
lists appear equally often in the better positions and the credited
share converges on the true 50/50 for equal teams. The trade is the
measured 3.6 percent variance increase: the same confidence-interval
width needs 3.6 percent more sessions. The naive alternative is not a
cheaper experiment — it is an experiment whose interval is tight around
the wrong answer, and a tight interval around the wrong center is a
confident wrong answer. Teams that randomize must also pre-register the
start and analyze the pooled comparison; the [credit-tie
detour](../when-the-credit-is-unbalanced/) covers the tie rule that
still has to be declared for shared documents, and the
[tiny-traffic detour](../when-the-traffic-is-tiny/) covers the
traffic budget that made interleaving necessary in the first place.

## Evidence boundary

The executed audit simulates position clicks over two declared disjoint
lists with equal teams (fixed seeds). It demonstrates the bias and its
measured cost; real interleaving also needs the tie rule, the pooled
statistical test over credits, and variance reduction for small effects
(Chapelle et al., 2012, TOIS), which this model does not include. The
position-click behavior follows Joachims et al. (2005, SIGIR) and the
interleaving sensitivity claims are attributed to Radlinski & Craswell
(2010, SIGIR).

## Check your mental model

Answer each before opening it.

**1. Why is a tight confidence interval not a sign the naive blend
worked?**

<details>
<summary>Answer</summary>

Because the interval is tight around the wrong value. At 200,000
sessions the naive interval is +/-0.23 percent around 59.3 percent, and
the true 50/50 is 78 standard errors outside it. The failure is a
fixed bias from the position click model, and sample size only shrinks
the interval around that bias — the experiment gets more confident in
the wrong answer, never closer to the truth.

</details>

**2. What does the random start actually cost, in the measured model?**

<details>
<summary>Answer</summary>

It raises the per-session outcome variance from 0.2413 to 0.2500 —
3.6 percent — so the same confidence-interval width needs 3.6 percent
more sessions. The empirical spread across 2,000 experiments matches
(0.99 percent vs 1.00 percent). The bias removal is the dominant
benefit; the variance cost is real but small.

</details>

## Next

Back to [stage 38](../). The
[credit-tie detour](../when-the-credit-is-unbalanced/) declares the
rule that keeps the credit honest when the teams share documents, and
the [tiny-traffic detour](../when-the-traffic-is-tiny/) shows the
traffic budget interleaving is built to beat.
