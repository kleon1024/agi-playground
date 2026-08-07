---
status: verified
level: applied
base: scratch
label: When the preference cycles
verified: 2026-08-07
---

# The preference the scalar model cannot hold

**Question:** [stage 32's recommendation RLHF](../) trains the ranker
from pairwise preferences under a Bradley-Terry scalar reward: every
item gets one score, and the score ranks them. This chapter asks what
happens when the observed preferences are not transitive — A beats B,
B beats C, C beats A — and reads how the scalar model fails on the
cycle.

**Before this:** [stage 32 — recommendation RLHF](../) and its
margin-stratified pair audit, which showed the near-tie pairs where
label noise decides the preference. A cycle is the limit of that
problem: the preference is a judgment call, and no single score can
hold it.

## The cycle, executed

The run ([record](runs/2026-08-07-cycle-read.md)) fits an Elo-style
scalar model to the three-item cycle A > B, B > C, C > A:

| pair | observed | predicted | probability |
|---|---|---|---:|
| A vs B | A wins | A wins | 0.34 |
| B vs C | B wins | B wins | 0.50 |
| C vs A | C wins | C wins | 0.66 |

Contradictions: 2 of 3 edges. The fitted ratings never settle — the
last-update swing after 1,000 iterations is 0.659, far from zero.

## The reading

A scalar model is transitive by construction: ratings that rank A above
B and B above C force A above C, but the observed data says C beats A.
The cycle has no consistent scalar answer, so the fit keeps rotating —
the swing does not decay, and at least one observed edge is always
predicted wrong. The fix is detection first: count cyclic triples among
the sampled pairs before trusting the fitted scores. Where cycles
exist, either drop the weakest edge — the one with the lowest measured
agreement — or model the preference as context-dependent instead of a
single score. A cycle is not a label-quality failure; it is evidence
that the preference itself depends on the set, which a global rank
cannot express.

## Evidence boundary

The executed fit over one hand-built three-item cycle (illustrative,
deterministic, Elo updates with logistic expectation). It demonstrates
the mechanism; real preference logs need the cyclic-triple count over
sampled pairs to decide whether non-transitivity is frequent enough to
justify a context-dependent model. Zhang et al., "Beyond Bradley-Terry
Models: A Review and Open Problems", ICML 2025, arXiv:2410.02197, is
the reference for the scalar model's limitation; Bertrand, Czarnecki
and Gidel, "On the Limitations of the Elo, Real-World Games are
Transitive, not Additive", UAI 2023, is the Elo-specific analysis.

## Check your mental model

Answer each before opening it.

**1. Why can no fitted score satisfy the cycle?**

<details>
<summary>Answer</summary>

Because a score is a rank, and a rank is a total order — transitive by
construction. Three ratings must put one item above the other two, but
the cycle says every item loses to exactly one other. The executed fit
shows the consequence: the ratings keep rotating (swing 0.659 after
1,000 iterations) and 2 of 3 observed edges are predicted wrong.

</details>

**2. What is the difference between a noisy preference and a cyclic
one?**

<details>
<summary>Answer</summary>

A noisy preference contradicts the truth because of label error; a
cyclic preference is the truth, but it depends on the set — A beats B
in one context and loses to it in another. The first is fixed by
cleaning or re-asking labels; the second is fixed by dropping the
weakest edge or modeling the preference as context-dependent, which is
exactly what a single scalar score cannot do.

</details>

## Next

Back to [stage 32](../), where the ranker learns which item the user
preferred — now with the checks that tell a clean label from a cyclic
one.
