# Run — multimodal recall, executed on the cold-item reachability model

**Date:** 2026-08-07
**Command:** `uv run python core/multimodal_recall.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 33 asks whether content vectors make cold items retrievable. This run checks which items are reachable from image and text embeddings.

## Output

```
multimodal recall, read:
  item_a: vectors ['image', 'text'], warm, reachable yes
  item_b: vectors ['image'], warm, reachable yes
  item_c: vectors ['image', 'text'], cold, reachable yes
  item_d: vectors ['text'], cold, reachable yes
  item_e: vectors ['none'], cold, reachable no
  cold items retrievable: 2/3

reading: a cold item is only retrievable if its content
produces a vector. The VLM is the cold-start bridge: image and
text embeddings make the never-clicked item reachable, which
is the frontier version of stage 01's content understanding.
```

## Notes

- Two of three cold items are retrievable; the one with no content vector is not.
- The VLM is the cold-start bridge: image and text embeddings make the never-clicked item reachable, the frontier version of stage 01's content understanding.
