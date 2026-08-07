---
status: verified
level: foundation
base: scratch
label: When the expert goes dead
verified: 2026-08-06
---

# The dead expert: what load balancing exists to fight

**Question:** [the MoE chapter](../) measured six routing configurations on
a toy with a 4:1 pattern skew. This chapter reads the recorded run and
asks what the counts column shows about the mechanism's failure mode.

**Before this:** [the MoE chapter](../) and its recorded routing sweep.

## The sweep, read

The run ([record](runs/2026-08-06-dead-expert-read.md)) reads the recorded
table:

| top-k | shared | accuracy | entropy | imbalance | routed counts |
|---:|---:|---:|---:|---:|---|
| 1 | no | 1.000 | 1.327 | dead expert | [45, 0, 6, 149] |
| 1 | yes | 1.000 | 1.362 | 21.5x | [172, 8, 11, 9] |
| 2 | no | 1.000 | 1.352 | 3.9x | [93, 144, 37, 126] |
| 2 | yes | 1.000 | 1.349 | 5.6x | [174, 56, 31, 139] |
| 4 | no | 1.000 | 1.240 | 1.0x | [200, 200, 200, 200] |
| 4 | yes | 1.000 | 1.270 | 1.0x | [200, 200, 200, 200] |

## Two readings

**Top-1 without a shared expert produces a dead expert — the routing analog
of codebook collapse.** Under the 4:1 skew, one expert never gets routed
(0/200) and another dominates (149/200). The mechanism is the same as
mission 07's codebook collapse: a softmax router concentrates mass on the
expert that fits the frequent pattern, the rare experts stop being chosen,
and nothing rebalances them. That is the imbalance (21.5x with a shared
expert, or a dead expert without one) that load-balancing losses and
Quantile Balancing exist to fight.

**Accuracy is 1.000 in every cell — routing does not buy accuracy, it buys
compute.** On a separable task, every configuration reaches perfect
accuracy; what differs is how much compute each input spends (one of four
experts at top-1, all four at top-4). The chapter's promise — capacity
grows with expert count while compute grows with top-k — is visible here,
and the imbalance column is the cost the promise hides.

## The fix and its trade

The dead expert is a routing problem, and the fix is a balancing term in
the training objective. **The auxiliary load-balancing loss** (Switch
Transformers: Fedus, Zoph & Shazeer, JMLR 23, 2022, arXiv:2101.03961)
penalizes the router for concentrating its mass, with a weight (alpha =
1e-2 in the original) that is the first trade knob: too weak and the
4:1 skew still wins (the measured dead-expert row), too strong and the
router stops choosing the expert that fits the input — routing quality
pays for fairness. **The capacity factor** is the serving-side half of the
same trade: it caps how many tokens an expert can take in a batch and
drops the overflow, which is how a balanced-looking router still loses
information under a skewed real distribution. **Quantile Balancing**
(DeepSeek-V3: Liu et al., 2024, arXiv:2412.19437) removes the auxiliary
loss and adds a bias term to the router logits from a histogram over
routing scores, targeting exactly the realized-count column this detour
reads — and its trade is the same one measured here, shifted: it balances
the counts the batch waits on rather than the probabilities the auxiliary
loss sees, at the cost of a per-step histogram pass. What none of the
three fixes does is change the input distribution: the 4:1 skew is still
there, and the balancing term is why the router's accuracy (1.000 in
every cell) does not drop when it is added.

## Evidence boundary

The recorded routing sweep (one toy, 4 experts, 4 patterns, one skew,
1,500 steps per configuration). It reads that artifact; it does not re-run
the toy and does not claim the imbalance transfers to production MoE
layers, where routing entropy and load balancing interact with real data
distributions.

## Check your mental model

Answer each before opening it.

**1. Accuracy is perfect in every cell. Why does the chapter treat the
dead expert as a failure?**

<details>
<summary>Answer</summary>

Because the toy is separable — every configuration reaches 1.000, so
accuracy cannot distinguish them. The failure is in the counts: one expert
at 0/200 means the router is not actually using the capacity the MoE
promises. On real, non-separable data, a dead expert is wasted capacity and
a hidden bottleneck, and the imbalance is the mechanism that produces it.

</details>

**2. Why does routing entropy stay near maximum even when the counts are
skewed?**

<details>
<summary>Answer</summary>

Because entropy is computed on the *softmax probabilities*, which stay
balanced in expectation, while the counts are the *realized* routes under a
4:1 pattern-frequency skew. The two are different diagnostics: entropy says
the router is not degenerate in its weights; the imbalance says the data
distribution still overloads one expert. Reading only one of them hides the
collapse.

</details>

## Next

Back to [the MoE chapter](../), or to
[the rung where MoE was measured](../../../01-language-model/02-pretrain/architecture-ablations/the-rung-that-flipped/)
which tests the same mechanism on a real decoder.
