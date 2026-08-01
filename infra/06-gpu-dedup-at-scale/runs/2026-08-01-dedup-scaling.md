# MinHash hashing time vs. LSH bucket-verification time, by corpus size

**Command:**

```bash
cd infra/06-gpu-dedup-at-scale/core
python3 dedup_scaling.py --sizes 1000,4000,16000,48000 --cluster-frac 0.10 --threshold 0.5
```

**Hardware:** MacBookPro18,3 (Apple Silicon, arm64), 10 CPU cores, macOS
15.6.1, local SSD.
**Software:** Python 3.11.14, stdlib only.
**Wall-clock:** 3m25.63s total (all four sizes, one process, no parallelism).
**Cost:** $0 (local lane, CPU only, no GPU used).

**Metrics (real output, unedited):**

```
cluster_frac=0.1 num_perm=64 bands=16
       n    hash_s  hash_us/doc   verify_s      pairs  max_bucket  near_dupes
    1000    1.4070      1406.99     0.0395       4079          51        3778
    4000    5.6428      1410.71     0.6416      66925         217       62816
   16000   22.8287      1426.80     9.9264    1080164         849     1009939
   48000   67.6506      1409.39    92.4045    9655349        2478     9028482

ratio of consecutive sizes (n growth vs verify_time growth):
  n x4.0: hash_time x4.01, verify_time x16.22
  n x4.0: hash_time x4.05, verify_time x15.47
  n x3.0: hash_time x2.96, verify_time x9.31
```

**Notes:**

- `hash_us/doc` (hashing time divided by corpus size) is flat at ~1.41ms/doc
  across all four sizes (1406.99 / 1410.71 / 1426.80 / 1409.39) — signature
  generation is `O(n)`, confirmed directly rather than assumed.
- `verify_time` grows 16.22x and 15.47x for the two 4x steps in `n`, and
  9.31x for the final 3x step — consistent with `O(k^2)` bucket-verification
  cost, since `max_bucket` (the largest LSH bucket, dominated by the
  synthetic duplicate cluster) itself grows with `n`: 51, 217, 849, 2478 —
  a 48.6x increase against a 48x increase in corpus size.
- **Crossover, measured not extrapolated:** at n=16,000, hash_time (22.83s)
  exceeds verify_time (9.93s), a 2.30x margin in hashing's favor. At
  n=48,000, verify_time (92.40s) exceeds hash_time (67.65s), a 1.37x margin
  in verification's favor. The crossover sits between these two measured
  points on this exact synthetic corpus (10% duplicate fraction, 120-word
  template, 64 permutations / 16 bands).
- `pairs_compared` (total unique cross-bucket pairs actually run through
  exact Jaccard) reached 9,655,349 at n=48,000 from a corpus of only 48,000
  documents — the volume of independent comparable work, not the document
  count, is what a GPU batch operation would actually be sized against.
- `near_dupes` (pairs whose true Jaccard >= 0.5, this run's threshold) is
  high relative to `pairs_compared` at every size (92.6% at n=1,000, 93.9%
  at n=4,000, 93.5% at n=16,000, 93.5% at n=48,000) because most of this
  toy's compared pairs come from the deliberately duplicated cluster, not
  from incidental band collisions between unrelated documents — a synthetic
  property of this corpus construction, not a claim about real-corpus
  false-positive rates.
- No GPU was used at any point in this run. No GPU-accelerated dedup system
  (NeMo Curator or otherwise) was benchmarked, run, or approximated — this
  measures only the CPU-side cost shape that motivates reaching for one.
