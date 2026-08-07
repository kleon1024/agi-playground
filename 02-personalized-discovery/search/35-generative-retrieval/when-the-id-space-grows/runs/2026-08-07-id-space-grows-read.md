# Run — when the ID space grows, executed on the decode-accuracy curve read

**Date:** 2026-08-07
**Command:** `uv run python core/id_space.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 35's generator emits doc IDs. This run sweeps corpus size and reads beam accuracy.

## Output

```
id space, read (beam accuracy by corpus size):
      100 docs: accuracy 0.98
    1,000 docs: accuracy 0.93
   10,000 docs: accuracy 0.84
  100,000 docs: accuracy 0.71

reading: the generator must emit exact IDs, and the odds of a
decode error grow with the vocabulary. Generative retrieval's
recall is a decode property, not an index property — the
scaling curve is the frontier constraint.
```

## Notes

- Accuracy falls from 0.98 at 100 docs to 0.71 at 100,000 — the odds of a decode error grow with the vocabulary.
- Generative retrieval's recall is a decode property, not an index property.
