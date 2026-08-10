---
status: verified
level: applied
base: scratch
label: When everything is equidistant
verified: 2026-08-07
---

# The embedding space that stopped separating

**Question:** [stage 20's dense retrieval](../) ranks by cosine
similarity. This chapter reads the executed case where the embedding
space degenerates — every vector points the same way, so similarity
stops separating meaning — and asks how the ranking survives.

**Before this:** [stage 20 — dense retrieval](../) and its executed
cosine model.

## The collapse, executed

The run ([record](runs/2026-08-07-isotropy-collapse-read.md)) scores
the same five documents against the same query in two spaces:

| document | healthy cosine | degenerate cosine |
|---|---:|---:|
| d1 relevant | +0.981 | +0.975 |
| d2 related | +0.800 | +0.980 |
| d3 other | +0.000 | +0.984 |
| d5 unrelated | +0.000 | +0.990 |
| d4 opposite | -1.000 | +0.988 |

## The reading

In the healthy space cosine spans the full range and the relevant
document wins. In the degenerate space all five documents sit inside
+0.975..+0.990 — the ranking is decided by noise offsets, and the
unrelated d5 outranks the relevant d1. This is anisotropy: word and
item embeddings trained with maximum likelihood-like objectives drift
into a narrow cone instead of spreading across the space. Ethayarajh,
Duvenaud and Hirst ("Towards Understanding Linear Word Analogies", ACL
2019) measure the anisotropy directly; Gao, He, Tan, Qin, Wang and Liu
("Representation Degeneration Problem in Training Natural Language
Generation Models", ICLR 2019) show the same collapse for trained
representations and connect it to the training objective.

The operational consequence is the one the search team has to catch:
the dense ranker still emits an order, so recall@k looks healthy while
the order itself has become a frequency prior. The fix is not to tune
the similarity threshold — it is to repair the space (contrastive or
debiased training objectives, or post-hoc whitening of the vectors)
and to audit the cosine range itself: if the served distribution of
similarities is a spike instead of a spread, the index is not ranking
anything.

## The fix and its trade

The fix is to repair the space — contrastive or debiased training
objectives, or post-hoc whitening — and to audit the cosine range
itself: if the served distribution of similarities is a spike instead
of a spread, the index is not ranking anything. The executed collapse
prices the failure: in the healthy space cosine spans the full range
(relevant d1 at +0.981, unrelated d5 at +0.000, opposite d4 at -1.000)
and the relevant document wins; in the degenerate space all five
documents sit inside +0.975..+0.990, the ranking is decided by noise
offsets, and the unrelated d5 outranks the relevant d1. Ethayarajh,
Duvenaud and Hirst (ACL 2019) measure the anisotropy directly; Gao et
al. (ICLR 2019) connect the collapse to the training objective.

The trade, named: contrastive objectives and debiasing cost training
data and compute, and whitening costs a post-processing transform — and
neither is a threshold-tuning shortcut, because the dense ranker still
emits an order, so recall@k looks healthy while the order itself has
become a frequency prior. The cosine-range audit is the cheap guard that
catches the spike before the index is trusted.

## Who owns the loop

- **The dense-retrieval model team** owns the space and its training
  objective — the anisotropy check is their shipping bar.
- **The serving and indexing team** owns the cosine-range audit on the
  served snapshot, so a collapsing space is caught in serving, not in
  the next retrain.
- **The evaluation team** owns the recall@k read that must be paired with
  an order sanity check, since recall alone certifies a frequency prior.

## Evidence boundary

The two hand-built concept spaces (illustrative, deterministic). They
demonstrate the collapse mechanism; real anisotropy is measured over
the trained embedding distribution, which this chapter does not train.

## Check your mental model

Answer each before opening it.

**1. Why does the degenerate space rank d5 above d1?**

<details>
<summary>Answer</summary>

Because every vector shares the same dominant component, the cosine is
nearly identical for all pairs, and the tiny unique offsets decide the
order. Those offsets are training noise, not meaning — so the ranking
is a frequency prior wearing a similarity label, and the relevant
document can rank below an unrelated one.

</details>

**2. How would you catch this in production?**

<details>
<summary>Answer</summary>

Audit the served distribution of similarities: a healthy space spreads
cosines across the range, a degenerate one spikes. If the spike is
there, the dense ranker is not ranking — fix the space (objective or
post-processing), not the threshold, and re-check the range.

</details>

## Next

Back to [stage 20](../), where the embedding is the retrieval index.
The [stale embedding detour](../when-the-embedding-is-stale/) covers
the item without a vector; this chapter covered the space where having
a vector stops meaning anything.
