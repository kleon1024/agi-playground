---
status: verified
level: reference
base: none
verified: 2026-08-01
label: GPU dedup at scale
---

# Why does dedup reach for a GPU once the corpus gets big enough?

**Question:** [the corpus release policy](../what-a-release-needs/#the-duplicate-threshold-you-set-without-meaning-to)
already explains MinHash + LSH banding as a CPU-bound mechanism, and
[mission 01's corpus pipeline](../)
runs it from scratch on 20,000 real pages. Both stop at the same place: LSH
band collisions are *candidates*, not confirmed duplicates, and neither
chapter runs the verification step that turns a band collision into a
decision. What does that verification step cost as the corpus grows, and
why does that cost — not the hashing — become the reason a real pipeline
reaches for a GPU?

**The artifact this chapter follows** is a real, measured CPU timing split:
hashing time versus within-bucket verification time, at four corpus sizes
(1,000 / 4,000 / 16,000 / 48,000 synthetic documents), showing the exact
point where verification overtakes hashing.

**Before this:** [what has to be true of text before you train on it?](../)
— you need the MinHash/LSH mechanism itself (shingles, signatures, banding,
the S-curve threshold) before this chapter's timing split means anything.
This chapter does not re-derive that mechanism; it measures the one step the
mechanism chapter left unmeasured.

## 1. A band collision is a candidate, not a verdict

[`01-language-model/00-corpus/core/pipeline.py`](../core/pipeline.py)'s
`MinHashDeduper` unions any two documents that share a full band signature
and stops there — it accepts the LSH threshold's false-positive rate
implicitly. A production pipeline cannot: the whole point of the S-curve in
[the corpus release policy](../what-a-release-needs/) is that a band
match at Jaccard 0.5 is a coin flip, not a duplicate. So real corpus-dedup
pipelines (Lee et al., "Deduplicating Training Data Makes Language Models
Better," ACL 2022; the RefinedWeb pipeline, Penedo et al. 2023) add a
verification pass: for every pair of documents that collide in the same LSH
band, compute their **exact** Jaccard similarity over the full shingle sets,
and only then decide.

That verification pass is the subject of this chapter. Hashing every
document once is `O(n)`. Verification is not — it is `O(k^2)` **per bucket**,
where `k` is however many documents happen to land in that bucket. Most
buckets are small (unrelated pages rarely share a full band by chance). But
templated, boilerplate-heavy web content — the exact case
[the corpus release policy](../what-a-release-needs/) names as the reason
exact-hash dedup is not enough — produces buckets whose size scales *with*
the corpus, not independently of it. That is what this chapter's `core/`
measures directly.

## 2. What the toy measures

[`core/dedup_scaling.py`](core/dedup_scaling.py) mirrors `MinHashDeduper`'s
exact mechanism (shingle sets, 64-permutation signatures, 16 bands of 4 rows
— the same settings [the corpus release policy](../what-a-release-needs/)'s
worked table uses) and adds the missing step: for every LSH bucket with more
than one member, it computes true pairwise Jaccard over the full shingle
sets and times that pass separately from signature generation.

The synthetic corpus is built to reproduce the real failure mode, not to
flatter it: 10% of each corpus is near-duplicate variants of one fixed
120-word template (a handful of words swapped per copy — the toy version of
"same boilerplate, different timestamp"), and the rest are independent
random documents with negligible mutual overlap. The dupe cluster's size
scales with corpus size, exactly as a fixed fraction of templated content
would at real web scale.

```bash
cd 01-language-model/00-corpus/dedup-at-scale/core
python3 dedup_scaling.py --sizes 1000,4000,16000,48000 --cluster-frac 0.10 --threshold 0.5
```

## 3. The measured crossover

```
cluster_frac=0.1 num_perm=64 bands=16
       n    hash_s  hash_us/doc   verify_s      pairs  max_bucket  near_dupes
    1000    1.4070      1406.99     0.0395       4079          51        3778
    4000    5.6428      1410.71     0.6416      66925         217       62816
   16000   22.8287      1426.80     9.9264    1080164         849     1009939
   48000   67.6506      1409.39    92.4045    9655349        2478     9028482
```

Per-document hashing cost (`hash_us/doc`) is flat across every corpus size —
about 1.41ms/doc regardless of `n`, exactly what `O(n)` predicts. Verification
time is not flat: it grows 15-16x for each 4x step in corpus size (`n x4.0:
... verify_time x16.22`, then `x15.47`), and 9.3x for the final 3x step —
consistent with the `O(k^2)` bucket cost, since the dupe cluster (and
therefore the biggest bucket) grows with `n`. `max_bucket` goes from 51 at
n=1,000 to 2,478 at n=48,000, a 48.6x increase against a 48x increase in `n`.

The crossover is real and measured, not extrapolated: at n=16,000, hashing
(22.8s) still costs more than verification (9.9s) — a 2.3x margin. At
n=48,000, verification (92.4s) costs *more* than hashing (67.7s) — the ratio
has flipped to 1.37x in verification's favor. Between those two points, on
this exact synthetic corpus, is where a real pipeline's dedup wall-clock
stops being dominated by "how many documents" and starts being dominated by
"how templated is the content."

Full trace: [`runs/2026-08-01-dedup-scaling.md`](runs/2026-08-01-dedup-scaling.md).

## 4. Why this motivates a GPU, not just a faster CPU loop

Hashing is embarrassingly parallel across documents with no shared state —
splitting it across CPU cores scales it near-linearly, which is why nobody
needs a GPU for the hashing half. Verification is embarrassingly parallel
too (every candidate pair is independent), but the *volume* of independent
work is what changed: at 48,000 synthetic documents with a 10% duplicate
fraction, this chapter's toy already produced 9.66 million candidate pairs
to check. Real pretraining corpora are not 48,000 documents — FineWeb
(Penedo et al., 2024) and RefinedWeb (Penedo et al., 2023) describe
deduplication over many hundreds of millions to billions of documents, at
which point candidate-pair counts in this same shape reach a scale where a
CPU core computing set intersections one pair at a time, however many cores
you add, stops being the economical way to spend compute.

NVIDIA's NeMo Curator (announced March 2024, "Curating Trillion-Token
Datasets: Introducing NVIDIA NeMo Curator") targets exactly this step: its
fuzzy-dedup module runs MinHash LSH candidate generation, then computes
Jaccard similarity over candidate pairs as batched GPU dataframe operations
via RAPIDS (cuDF), and groups confirmed duplicates into clusters with
cuGraph's connected-components implementation — GPU-parallel primitives
built for exactly the "many independent pairwise comparisons" shape this
chapter's `verify_time` column measures on CPU. The mechanism doesn't change;
what changes is how many comparisons per second the hardware can retire.

## 5. What this does not establish

**No GPU was used anywhere in this chapter, and no GPU speedup is measured.**
This is a CPU-side timing study showing *why* the bottleneck shifts as corpus
size grows — it is not a benchmark of NeMo Curator, RAPIDS, or any GPU
dedup pipeline, and it makes no claim about how many times faster a GPU
verification pass would be. That number needs a real GPU run, which belongs
on the Modal lane per [the compute-lane guides](../../../reference/modal.md)'s decision table, and
is not attempted here.

**No real corpus was deduplicated.** The synthetic corpus is built to put a
scaling duplicate cluster in view quickly; it says nothing about the true
duplicate rate, bucket-size distribution, or verification cost of any real
crawl. [Mission 01's corpus pipeline](../)
is the chapter that measures a real, bounded 20,000-page sample; this chapter
only asks how that sample's cost would compound at larger `n`.

**The crossover point (between n=16,000 and n=48,000 here) is a property of
this toy's 10% duplicate fraction and 120-word template, not a universal
constant.** A corpus with a smaller duplicate fraction pushes the crossover
to a larger `n`; a corpus with more templated boilerplate pulls it closer.
Recompute it for your own duplicate rate before treating any specific `n` as
a threshold.

## A brief history

Broder introduced MinHash in 1997 ("On the Resemblance and Containment of
Documents," SEQUENCES '97) at AltaVista, to detect near-duplicate web pages
without comparing every pair. LSH banding for approximate similarity search
followed shortly after (Indyk and Motwani, 1998). Both ideas are decades
older than the trillion-token pretraining corpora that made their
verification-cost bottleneck economically significant enough to move to a
GPU: Lee et al. (2022) ran MinHash LSH dedup across the C4 and RealNews
corpora and reported measurable downstream model improvements from removing
near-duplicates; RefinedWeb (Penedo et al., 2023) and FineWeb (Penedo et al.,
2024) describe the same MinHash LSH pipeline run at web-crawl scale as part
of their published data recipes; NeMo Curator (NVIDIA, March 2024) is the
first widely documented GPU-accelerated implementation of the verification
step this chapter isolates.

## Exercises

1. **Change `--cluster-frac`.** Halve it to 0.05 and double it to 0.20, at
   the same four sizes. Does the crossover point move in the direction the
   `O(k^2)`-per-bucket explanation predicts?
2. **Change the bands/rows split.** The corpus release policy's S-curve table
   shows that 16 bands of 4 rows puts the 50% recall threshold at Jaccard
   0.5. Try `--bands 8` (8 rows per band, a stricter threshold) at the same
   sizes — does `max_bucket` shrink, and does that measurably delay the
   crossover?
3. **Read `MinHashDeduper.add()` again.** It never runs a verification step
   at all — it treats every band collision as a confirmed duplicate. Using
   this chapter's own `near_dupes` vs `pairs_compared` columns, estimate how
   many of mission 01's real merged clusters could be false-positive band
   collisions that a verification pass would have split back apart.

## Run it

```bash
cd 01-language-model/00-corpus/dedup-at-scale/core
python3 dedup_scaling.py --sizes 1000,4000,16000,48000 --cluster-frac 0.10 --threshold 0.5
```

CPU only, stdlib only (`hashlib`-free — reuses Python's built-in `hash()` the
same way `MinHashDeduper` does), about 3.5 minutes total wall-clock, \$0. Full
trace: [`runs/2026-08-01-dedup-scaling.md`](runs/2026-08-01-dedup-scaling.md).

A detour from here: [hashing scales linearly; verification scales
quadratically](when-verification-goes-quadratic/) — the recorded scaling
read: corpus x4 grows hash time x4.01 and verify time x16.22, because
verification checks pairs (n^2), not documents (n) — the LSH trade.
