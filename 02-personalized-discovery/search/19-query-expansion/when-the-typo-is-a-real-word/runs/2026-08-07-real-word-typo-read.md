# Run — the typo that is a real word

**Date:** 2026-08-07
**Command:** `uv run python core/real_word_typo.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Show the class of misspelling that string-level correction cannot
detect: a typo that is itself a valid catalog term. The check "is this
token known?" passes, so edit distance never fires and the retrieval
path serves the wrong category.

## Output

```
real-word typo, read:
  query 'shorts' is a catalog term: True
  nearest edit-distance candidates: shorts (0), shirts
  correction fires: no — the token is already in the vocabulary

reading: string-level correction cannot see this error. The
query is a real word, so edit distance passes it unchanged and
BM25 serves shorts to a user who wanted shoes. The evidence
that it is a typo lives outside the string — the click log and
query co-occurrence — which is why production correction adds
log evidence on top of distance.
```

## Notes

- The distance to the intended word is irrelevant: correction only runs
  on unknown tokens, and `shorts` is known. The error is invisible to
  every string-level check. Even the distance ranking points the wrong
  way — `shirts` (distance 1) is nearer than the intended `shoes`
  (distance 2), so a hypothetical corrector would repair toward the
  wrong word anyway.
- The evidence lives in the click log — a `shorts` query that clicks
  shoe results — not in the lexicon. Hirst and Budanitsky, "Correcting
  real-word spelling errors by restoring lexical cohesion", Natural
  Language Engineering 11(1), 2005, formalize the same class: real-word
  errors are only detectable from context.
- The operational trap: a `shorts` query that returns shorts results
  looks healthy on the zero-result rate and click-through, so the miss
  is invisible to the funnel until a user types `shoes` instead.
