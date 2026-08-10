---
status: verified
level: applied
base: scratch
label: When the gain is below the fold
verified: 2026-08-07
---

# The improvement the page never shows

**Question:** [stage 22's reranking](../) reorders the first stage's
top candidates, and the page serves three slots. This chapter reads the
executed case where the reranker's fixes land in the middle of the list
— the offline metric improves while the served top-3 gets worse — and
asks which k the team is actually optimizing.

**Before this:** [stage 22 — reranking](../) and its executed reorder
model.

## The divergence, executed

The run ([record](runs/2026-08-07-below-fold-read.md)) scores one
10-position grade list before and after reranking:

| order | NDCG@10 | NDCG@3 |
|---|---:|---:|
| first stage | 0.9592 | 1.0000 |
| reranked | 0.9758 | 0.9677 |

## The reading

The reranker promoted a grade-2 document buried at position 10 up to
position 4 and fixed the middle of the list — NDCG@10 improves from
0.9592 to 0.9758. To do that it mis-swapped positions 2 and 3, so the
three-slot page shows a worse top-3: NDCG@3 falls from 1.0000 to
0.9677. The offline experiment approves the reranker; the served
surface says it hurt. The gap between the eval k and the served k is
the failure — gains below position 3 are counted as shipped value that
no user ever sees.

This is the operational version of the k choice: Nogueira and Cho
("Passage Re-ranking with BERT", arXiv:1901.04085, 2019) show the
cross-encoder reranker that production systems actually deploy, and
that model is expensive enough that it runs on a shortlist — the
served page is even shorter. Every reranker ship needs the same check:
report at the served k, audit per position, and slice the experiment
by head and tail, because the tail is where the rich features misfire
at the top (the stage's own [served-k audit](../runs/2026-08-07-rerank-audit.md)
measures that slice collapsing at @3 while improving at @10).

## The fix and its trade

The fix is to report at the served k and audit per position — gains below
the fold are not shipped value. The executed divergence prices the
failure: the reranker promotes a grade-2 document from position 10 to 4,
fixing the middle of the list (NDCG@10 improves 0.9592 to 0.9758), but
mis-swaps positions 2 and 3, so the three-slot page shows a worse top-3
(NDCG@3 falls 1.0000 to 0.9677). The offline experiment approves the
reranker; the served surface says it hurt.

The trade, named: the cross-encoder reranker (Nogueira and Cho 2019) is
expensive enough that it runs on a shortlist, and the served page is
even shorter — so the k gap between eval and serving is where the
reranker's value leaks. Every ship needs the same check: report at the
served k, audit per position, and slice by head and tail, because the
tail is where rich features misfire at the top while the aggregate
stays positive.

## Who owns the loop

- **The evaluation and product team** owns the surface contract — what k
  the page actually serves, and the @10-versus-@3 audit.
- **The ranking team** owns the served-k evaluation that decides whether
  a rerank change ships.
- **The serving team** owns the pool size that defines what the reranker
  is allowed to reorder.

## Evidence boundary

The executed comparison over one hand-built grade list (illustrative,
deterministic). It demonstrates the k-divergence mechanism; real
served-k evaluation runs over the production ranking and its labels.

## Check your mental model

Answer each before opening it.

**1. How can the reranker improve NDCG@10 while hurting NDCG@3?**

<details>
<summary>Answer</summary>

By fixing positions 4-10 while making a top-3 mistake. The buried
grade-2 promoted to position 4 is a real gain that NDCG@10 counts; the
mis-swap at positions 2-3 is a loss that only NDCG@3 sees. The same
reorder improves one metric and degrades the other because the two
metrics look at different parts of the list.

</details>

**2. What should the eval report look like before shipping a
reranker?**

<details>
<summary>Answer</summary>

It should report at the served k first, then at the eval k, with a
per-position audit and a head/tail split. If the served-k delta is
negative, the reranker is not ready regardless of what @10 says —
gains below the fold do not reach users.

</details>

## Next

Back to [stage 22](../), where the reranker refines what the first
stage recalled. The [budget detour](../when-the-rerank-budget-is-tight/)
covers the cutoff that decides what the reranker can see; this chapter
covered the k that decides whether the user ever sees what it did.
