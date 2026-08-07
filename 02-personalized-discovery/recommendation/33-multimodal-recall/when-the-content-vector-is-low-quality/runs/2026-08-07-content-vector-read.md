# Run — when the content vector is low quality, executed on the noisy-embedding read

**Date:** 2026-08-07
**Command:** `uv run python core/low_quality_vector.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 33 makes cold items reachable through content vectors. This run
embeds 12 items across four categories — two clean items per category
(embedding noise 0.08) and one low-quality item per category (noise
0.70, standing in for the blurry image or the auto-tag text) — and
measures recall@3 per quality stratum.

## Output

```
low-quality content vectors, read (recall@3):
  category A: top-3 ['A1', 'A2', 'A3']  (items A1, A2, A3*, * = low-quality content)
  category B: top-3 ['B1', 'B2', 'B3']  (items B1, B2, B3*, * = low-quality content)
  category C: top-3 ['C2', 'C1', 'D2']  (items C1, C2, C3*, * = low-quality content)
  category D: top-3 ['D1', 'D2', 'B3']  (items D1, D2, D3*, * = low-quality content)
  recall@3: clean 8/8, low-quality 2/4

reading: has a vector is not has a usable vector. The
low-quality item is in the index, but its noisy embedding
sits far from its category and loses the retrieval race to
other categories' items. Reachability is a quality property,
not a presence property: gate content quality before
embedding and re-embed when the source improves.
```

## Notes

- Clean items recall 8/8: at small noise the vector stays near its
  category centroid and wins the category query every time.
- Low-quality items recall 2/4: the noisy vector wins its own category
  when the noise happens to stay near the centroid (A3, B3) and loses
  the race when it drifts (C3, D3). Displacement is a lottery, not a
  guarantee — which is exactly why the defect shows only on the
  per-stratum split, not on the aggregate reachable figure.
- The displaced items lose to other categories' items: D2 enters
  category C's top-3 and B3 enters category D's top-3. The noise pulls
  the ranking across category boundaries, so the same failure degrades
  both recall and precision.
- The fix is a content-quality gate before embedding (blur, resolution,
  caption coverage, auto-tag confidence) plus re-embedding when the
  source improves. Radford et al. 2021 (arXiv:2103.00020) is the
  two-encoder reference; Liang et al. 2022 (arXiv:2203.02053) is the
  modality-gap reference that explains why a displaced vector is not
  cheap to repair in the embedding space itself.
