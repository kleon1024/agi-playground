# Run — the modality-coverage audit over the item log

**Date:** 2026-08-07
**Command:** `uv run python core/multimodal_recall.py --emit-log /tmp/modality-coverage-envelope.json` then `uv run python prod/modality_coverage_audit.py /tmp/modality-coverage-envelope.json`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib and pandas.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Stage 33 makes cold items retrievable through content vectors. The
failure mode this audit exists for is the single-modality item: an item
with one vector is reachable through one surface only, so a query of
the missing modality can never see it. The audit stratifies a 20-item
log by modality coverage and reports the per-surface reachability —
the case-finding that shows which items a given query surface cannot
retrieve.

## Output

```
modality-coverage audit over the 20-item log:
  aggregate reachable (either modality): 100%

  stratum  items  image  text  both  single
  head     10     100%   100%   100%  0%
  tail     10     50%   50%   0%  100%

verdict: SINGLE-MODALITY ITEMS ARE HALF-REACHABLE --
head items carry both vectors (100%) and
are reachable through either surface. Tail items are
single-modality (100%): image-only items
are invisible to text queries and text-only items
to image queries. The aggregate reachable figure of 100%
hides that half the query surfaces miss every tail item.
Report coverage per modality, and for a single-modality
item fall back to the modality it has or synthesize the
missing one (Radford et al. 2021; Liang et al. 2022).
```

## Notes

- The audit cohort is a 20-item log with the modality vectors per item.
  Head items carry both image and text vectors (100% both, 0% single);
  tail items carry exactly one (50% image, 50% text, 100% single).
- The aggregate reachable figure of 100% hides the failure: image-only
  items are invisible to text queries and text-only items to image
  queries, so half the query surfaces miss every tail item.
- Radford et al., "Learning Transferable Visual Models From Natural
  Language Supervision", ICML 2021, arXiv:2103.00020, is the
  two-encoder reference — the space that makes cross-modal retrieval
  possible. Liang et al., "Mind the Gap: Understanding the Modality
  Gap in Multi-modal Contrastive Representation Learning", NeurIPS
  2022, arXiv:2203.02053, is the modality-gap reference — image and
  text vectors sit in disjoint cones, which is why the missing
  modality is expensive to synthesize and why the per-surface
  coverage report has to be explicit.
