# Run — the space where everything is equidistant

**Date:** 2026-08-07
**Command:** `uv run python core/isotropy_collapse.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Show the anisotropy failure: when every vector carries the same
dominant component, cosine converges toward one value and the dense
ranking stops separating meaning.

## Output

```
isotropy collapse, read (cosine to the query vector):
  healthy space:
    d1 relevant  +0.981
    d2 related   +0.800
    d3 other     +0.000
    d5 unrelated +0.000
    d4 opposite  -1.000
  degenerate space:
    d5 unrelated +0.990
    d4 opposite  +0.988
    d3 other     +0.984
    d2 related   +0.980
    d1 relevant  +0.975

reading: in the healthy space cosine separates d1 (+0.981) from
d4 (-1.000) across the full range. In the degenerate space all
five sit inside +0.975..+0.990, the ranking is decided by tiny
noise offsets, and the unrelated d5 (+0.990) outranks the
relevant d1 (+0.975). The embedding has stopped being a
retrieval index — it is a frequency order with a similarity
label on top.
```

## Notes

- The healthy space spans the full cosine range and ranks the relevant
  document first; the degenerate space packs all five into +0.975..+0.990
  and inverts the order. The dense ranker still emits an order, so
  recall@k looks healthy while the order is a frequency prior.
- Anisotropy is measured, not assumed: Ethayarajh, Duvenaud and Hirst,
  "Towards Understanding Linear Word Analogies", ACL 2019, document
  embeddings clustering in a narrow cone; Gao, He, Tan, Qin, Wang and
  Liu, "Representation Degeneration Problem in Training Natural
  Language Generation Models", ICLR 2019, tie the collapse to the
  training objective.
- The production check is the served similarity distribution: a spike
  instead of a spread means the index is not ranking; the fix is the
  space (objective or post-hoc whitening), not the threshold.
