# Run — phrase ID ambiguity, executed on the substring match count

**Date:** 2026-08-07
**Command:** `uv run python core/phrase_id.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 35 decodes document IDs. This run counts how many documents a
phrase ID can name in a corpus of eight titles — the ambiguity that the
ID format decides.

## Output

```
phrase id, read (substring match ambiguity):
  emitted phrase        docs named
  search               5
  memory               5
  transformer memory   1
  sparse representations 1

reading: an atomic ID names one document, so the decode is
unambiguous. A phrase ID reads naturally but can name many
documents at once — the model emits 'search' and the corpus
offers five candidates, so a substring index has to resolve
which document the phrase meant.
```

## Notes

- "search" and "memory" each name 5 of 8 titles; the more specific
  phrases name exactly one. The ID format decides the ambiguity.
- Atomic docids (DSI; Tay et al., NeurIPS 2022) are unambiguous but must
  be memorized; phrase docids (SEAL; Bevilacqua et al., NeurIPS 2022)
  are easy to generate but need a substring index to resolve.
