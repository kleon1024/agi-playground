---
status: verified
level: foundation
base: scratch
label: Mixture of experts
verified: 2026-08-06
---

# Why route at all? The mixture-of-experts mechanism

**Question:** a mixture of experts keeps many small networks and routes each
input to a subset — capacity grows with the number of experts while compute
grows with the number routed to. What does that actually buy, and what are
the failure modes the production line spends its time fixing?

**Before this:** [the decoder block](../00-attention/) and
[the optimization loop](../02-optimization/). This chapter is the expert
block the way 00-attention is the attention block: a mechanism that holds
regardless of mission.

## The promise, stated once

One dense network of N parameters costs N FLOPs per input. An MoE with E
experts of N/E parameters each costs only top-k of them per input — so the
model can hold E times the capacity while spending k/E times the compute.
The bet is that the router can learn to send each input to the experts that
know it, which is what makes capacity without compute real instead of a
bookkeeping trick.

## The mechanism, measured on a toy

The toy ([run record](runs/2026-08-06-moe-routing.md)) isolates the
variables: 4 experts, 4 input patterns, pattern 0 four times as frequent,
and the six configurations of top-k (1, 2, 4) by shared expert (on, off):

| top-k | shared | accuracy | routing entropy | load imbalance | routed counts |
|---:|---:|---:|---:|---:|---|
| 1 | no | 1.000 | 1.327 | dead expert | [45, 0, 6, 149] |
| 1 | yes | 1.000 | 1.362 | 21.5x | [172, 8, 11, 9] |
| 2 | no | 1.000 | 1.352 | 3.9x | [93, 144, 37, 126] |
| 2 | yes | 1.000 | 1.349 | 5.6x | [174, 56, 31, 139] |
| 4 | no | 1.000 | 1.240 | 1.0x | [200, 200, 200, 200] |
| 4 | yes | 1.000 | 1.270 | 1.0x | [200, 200, 200, 200] |

<!-- interactive: MoERouting -->

Three readings:

**Routing buys compute, not accuracy.** Every cell hits 1.000 on this
separable task. The task is solvable by one expert; the MoE's value is that
top-1 and top-2 route a quarter and a half of the experts per input and
still solve it — the accuracy is the floor, the compute is the point.

**Top-1 under skew kills an expert.** With pattern 0 four times as frequent,
the top-1 router routes expert 1 nowhere (0/200) and expert 3 to 74% of
inputs. This is the routing analog of codebook collapse: a never-routed
expert gets no gradient from its inputs and stays dead, exactly the failure
the codebook chapter measures for quantization. The dead expert is why
production MoEs run load-balancing losses and, in K3's case, Quantile
Balancing.

**Entropy and realized imbalance disagree.** Routing entropy sits near its
maximum (1.33-1.36 of ln 4 = 1.386) in every cell while the realized counts
are skewed up to 21.5x. The softmax router balances in expectation; the
realized distribution is what the hardware waits on, which is why
load-balancing targets the realized counts, not the entropy.

## The production line, in this repo's terms

The lineage ([the language-model line](../../01-language-model/lineage.md))
names what the frontier added to this toy's three variables. **SwiGLU** is
the expert shape (its gate can align with the linear and explode, which K3
answers with SiTU plus a softcap). **LatentMoE** inserts a down-projection
before routing and an up-projection after, so the same compute serves more
experts — with the four-matrix chain instability that one RMS Norm at the
up-projection input stabilizes. **Quantile Balancing** replaces the older
auxiliary-loss family with a histogram-approximated quantile over routing
scores (1,000 bins), targeting exactly the realized-count imbalance this
toy shows at top-1. And the **shared expert** — this toy's null — absorbs
common structure in real stacks so routed experts can specialize on the
difference, a benefit the toy's block-disjoint patterns never require.

## Evidence boundary

One toy task, six configurations, one seed: it shows routing's compute-for-
accuracy trade, the top-1 dead expert, and the entropy-versus-imbalance gap
on this separable setup. It does not show quality gains from more experts
(the toy is too easy), the shared expert's value (the toy has no common
structure), or the production line's stability fixes — those are the
attributed frontier results in the lineage.

## Check your mental model

Answer each before opening it.

**1. Why does the top-1 router kill an expert instead of balancing the 4:1
skew?**

<details>
<summary>Answer</summary>

Because the router optimizes accuracy, not fairness: routing pattern 0 to
one expert and everything else to others is already optimal, so the
frequent pattern's expert absorbs most inputs and one expert never wins.
Load balancing is a constraint the training objective has to add — no
auxiliary loss or quantile target, no balance — which is exactly why the
production line carries one.

</details>

**2. Routing entropy is near maximum while the realized counts are skewed
21.5x. How can both be true?**

<details>
<summary>Answer</summary>

Entropy averages the router's probability mass over all inputs, so a router
that assigns 0.25 mass to each expert in expectation scores near maximum
even when the *realized* winner per input concentrates on one expert. The
two measure different things — expected mixing versus realized assignment —
and hardware waits on the realized assignment, which is why
load-balancing targets counts, not entropy.

</details>

## Next

Back to the foundations index, or forward to
[the language-model lineage](../../01-language-model/lineage.md)
where this mechanism's frontier forms (LatentMoE, SiTU, Quantile Balancing)
are traced to the papers that introduced them.

A detour from here: [the dead expert: what load balancing exists to
fight](when-the-expert-goes-dead/) — the recorded routing sweep read:
top-1 under a 4:1 skew leaves one expert at 0/200 (the routing analog of
codebook collapse), and accuracy stays 1.000 in every cell because routing
buys compute, not accuracy.
