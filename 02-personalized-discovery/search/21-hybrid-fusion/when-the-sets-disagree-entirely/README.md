---
status: verified
level: applied
base: scratch
label: When the sets disagree entirely
verified: 2026-08-07
---

# Fusion with no agreement to reward

**Question:** [stage 21's hybrid fusion](../) promises coverage from
two matchers, and rewards the documents both agree on. This chapter
reads the executed case where the two sets are disjoint — no overlap,
no agreement — and asks what the fused list is then saying.

**Before this:** [stage 21 — hybrid fusion](../) and its executed
reciprocal-rank-fusion model.

## The disjoint case, executed

The run ([record](runs/2026-08-07-disjoint-sets-read.md)) fuses two
disjoint four-document lists:

| fused rank | doc | source | score |
|---|---:|---|---:|
| 1 | d1 | lexical#1 | 0.0164 |
| 2 | d5 | dense#1 | 0.0164 |
| 3 | d2 | lexical#2 | 0.0161 |
| 4 | d6 | dense#2 | 0.0161 |

## The reading

Every document in the fused list is present in exactly one matcher's
set, so there is nothing for the fusion to reward: reciprocal rank
fusion's signal is agreement — Cormack, Clarke and Büttcher ("Reciprocal
Rank Fusion Outperforms Condorcet and Individual Rank Learning
Methods", SIGIR 2009) show RRF beating rank-learning methods precisely
because it rewards the documents several rankings place highly. With
disjoint sets that signal is empty. The two rank-1 documents tie
(both 1/61), and the page order between them is a coin flip between the
lexical prior and the dense prior.

The operational question is not "which fusion weight" — it is whether
the matchers are answering the same query at all. A disjoint result
usually means one matcher silently failed to understand the query (a
vocabulary gap in one, a sparse tail in the other), and fusion papered
over it. The check is overlap rate: when the served overlap collapses,
the fused list has stopped being a consensus and become an
interleaving.

## The fix and its trade

The fix is to monitor the served overlap rate — when the overlap
collapses, the fused list has stopped being a consensus and become an
interleaving, and the system must know. The executed disjoint case
prices why: with two disjoint four-document lists, every fused entry
comes from exactly one matcher, the two rank-1 documents tie (both
1/61), and the page order between them is a coin flip between the
lexical prior and the dense prior. RRF's signal is agreement — Cormack,
Clarke and Büttcher (SIGIR 2009) show it beating rank-learning methods
precisely because it rewards documents several rankings place highly —
and with disjoint sets that signal is empty.

The trade, named: overlap monitoring costs a served-overlap read on the
query distribution, and the alternative is a fused page that papers
over a matcher failure — a disjoint result usually means one matcher
silently failed to understand the query (a vocabulary gap in one, a
sparse tail in the other). The operational question is not which fusion
weight; it is whether the matchers are answering the same query at all.

## Who owns the loop

- **The evaluation and relevance team** owns the overlap-rate monitor
  over the served query distribution.
- **The retrieval teams** own the matcher health the disjoint signal
  implicates — a collapsed overlap is a retrieval failure wearing a
  fusion artifact.
- **The fusion team** owns the empty-agreement detection and the alert
  that fires before the interleaved page ships.

## Evidence boundary

The executed fusion over two hand-built disjoint lists (illustrative,
deterministic). It demonstrates the empty-agreement mechanics; real
overlap-rate monitoring runs over the served query distribution.

## Check your mental model

Answer each before opening it.

**1. Why do the two rank-1 documents tie in the fused list?**

<details>
<summary>Answer</summary>

Because reciprocal rank fusion scores each document by the positions it
holds across the lists, and each document here appears in exactly one
list. The two rank-1 documents each contribute 1/(60+1) from their
single list — identical scores, so the fused top is a tie and the page
order between them is arbitrary.

</details>

**2. What should the team check when the fused list is disjoint?**

<details>
<summary>Answer</summary>

Whether the matchers were answering the same query. A disjoint result
usually means one matcher failed — a vocabulary gap in one, a sparse
tail in the other — and fusion hid it. Monitor the served overlap rate;
when it collapses, the list is an interleaving of two priors, not a
consensus.

</details>

## Next

Back to [stage 21](../), where the fusion weight is a trust decision.
The [empty-set detour](../when-one-set-is-empty/) covered the matcher
that returns nothing; this chapter covered the case where both return
something but cannot agree.
