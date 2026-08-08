---
status: verified
level: applied
base: scratch
label: When verification goes quadratic
verified: 2026-08-06
---

# Hashing scales linearly; verification scales quadratically

**Question:** [the dedup chapter](../) ran MinHash hashing and LSH bucket
verification at corpus sizes 1k to 48k. This chapter reads the recorded
scaling run and asks why the two halves of the pipeline grow so
differently.

**Before this:** [the dedup chapter](../) and its recorded scaling run.

## The scaling, read

The run ([record](runs/2026-08-06-dedup-read.md)) reads the recorded table:

| corpus | hash time | verify time | pairs checked |
|---:|---:|---:|---:|
| 1,000 | 1.41s | 0.04s | 4,079 |
| 4,000 | 5.64s | 0.64s | 66,925 |
| 16,000 | 22.83s | 9.93s | 1,080,164 |
| 48,000 | 67.65s | 92.40s | 9,655,349 |

Corpus x4: hash time x4.01, verify time x16.22.

## Two readings

**Hashing is per-document; verification is per-pair.** Every document gets
its MinHash signatures once, so hash time grows linearly with corpus size
(x4.01 for x4). Verification, though, checks the documents that landed in
the same LSH bucket — and the pair count inside buckets grows with n^2,
which is why verify time grows x16.22 for the same x4 corpus. The two
halves of the pipeline have different scaling laws, and the recorded rows
make them impossible to confuse.

**The LSH trade is accepting false negatives to keep the pair explosion
bounded.** At 48k, verification has already overtaken hashing (92.4s vs
67.7s) — without bucketing, the pair count would be n^2 over the whole
corpus, far worse. LSH is the bargain that keeps the verify step near the
hash step for as long as possible, and the near-dupe column (9 million at
48k) is the price: it checks the pairs the bucketing kept, not the ones it
dropped.

## The fix and its trade

The fix is to keep the two halves on different scaling laws and never let
verification inherit the corpus's growth. Three moves, in the order a real
pipeline meets them: LSH bucketing first (the band and row counts set the
threshold and therefore the candidate rate), exact verification only on the
candidates the buckets kept, and a verification tier that samples or
parallelizes once the pair count stops fitting the budget. The measured
curve is the argument for the first two: hashing at 48k is 67.65s and stays
near-linear, while verify at 92.40s has already overtaken it and grows x16
for every x4 of corpus — so the half of the pipeline that scales
quadratically is the one that must be bounded before it is parallelized.

The trade is false negatives for a bounded pair count. The LSH threshold
((1/16)^(1/4) = 0.50 at 16 bands of 4 rows) is the similarity below which
near-duplicates stop being checked, so documents the buckets separate are
never compared no matter how similar they are. Raising the threshold (more
bands) catches more duplicates and pays in candidate pairs; lowering it
misses more and pays in corpus inflation downstream — a decision that
belongs in the dataset record, because it reclassifies documents as
duplicates without anyone deciding to. The second trade is certainty for
verification cost: exact Jaccard on every candidate removes the false
positives the sketch introduced and costs the 92.4s, which is why a pipeline
that only needs an approximate keep-rate samples or runs a cheaper second
pass. The third is the capacity decision the recorded curve does not
measure: one process at 48k already spends more than a minute verifying, so
the point where hashing moves to GPUs or verification spreads across nodes
is a cost the record leaves for the infrastructure owner to size.

## Who owns the loop

- **The data-pipeline team** owns the threshold as policy, not tuning: the
  band and row counts — and therefore the 0.50 halfway point — belong in the
  dataset record, because changing them moves documents between the
  duplicate and unique buckets without anyone making the call.
- **The infrastructure team** owns the scaling decision: when verify time
  overtakes hash time (the 48k crossing), the x16-for-x4 growth is a
  capacity question — more nodes, a sampling tier, or a cheaper second
  pass — and the recorded curve is what sizes it.
- **The corpus owner** owns the false-negative budget: which near-duplicate
  band the pipeline may miss, and which duplicates are expensive enough
  downstream (benchmark leakage, train/test contamination) to justify
  checking at a lower threshold.

## Evidence boundary

The recorded scaling run (sizes 1k-48k, cluster fraction 0.1, 64
permutations, 16 bands, one process, stdlib-only). It reads that artifact;
it does not re-run the pipeline and does not extend the curve to GPU
lanes, which the chapter discusses as the point where the hashing half
moves to hardware.

## Check your mental model

Answer each before opening it.

**1. Why does verification grow with n^2 while hashing grows with n?**

<details>
<summary>Answer</summary>

Because they count different things. Hashing processes one document per
unit of work — linear. Verification processes pairs that share a bucket,
and the number of pairs among n documents scales with n^2. The recorded
x4.01 versus x16.22 is exactly that difference: quadruple the corpus,
quadruple the hashing work, but sixteen times the pairwise verification.

</details>

**2. What does "bounded false-negative risk" mean for the near-dupe
count?**

<details>
<summary>Answer</summary>

It means the pipeline deliberately misses some near-duplicates to keep the
pair count tractable. LSH buckets documents by signature bands, so two
documents that are near-duplicates but fall into different buckets are never
checked — that is the false negative. The near-dupe column (9 million at
48k) is what the bucketing *kept*; the dropped ones are the accepted cost
of not checking all n^2 pairs.

</details>

## Next

Back to [the dedup chapter](../), or to
[the corpus stage](../../) where
the same dedup question appears at mission scale.
