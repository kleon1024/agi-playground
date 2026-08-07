# Run — when the generator hallucinates, executed on the corpus-check read

**Date:** 2026-08-07
**Command:** `uv run python core/hallucinated_id.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 35's generator can emit IDs that do not exist. This run checks each generated ID against the corpus.

## Output

```
hallucinated id, read:
  generated doc_02: in corpus True
  generated doc_99: in corpus False
  generated doc_03: in corpus True
  valid results: ['doc_02', 'doc_03']

reading: doc_99 is emitted but does not exist, so the beam
slot is wasted and the result is dropped at the corpus check.
A retrieval model that manufactures IDs needs the check — the
index is the arbiter of what the generator may return.
```

## Notes

- doc_99 is emitted but does not exist, so the beam slot is wasted and the result is dropped at the corpus check.
- A retrieval model that manufactures IDs needs the check — the index is the arbiter of what the generator may return.
