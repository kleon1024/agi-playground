# Run — trust and explainability, executed on the contribution read

**Date:** 2026-08-07
**Command:** `uv run python core/attribution.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 52 introduces explanation quality. This run attributes one shown
item's score to its features and marks which claims the user can verify.

## Output

```
trust and explainability, read (contributions to the score):
  price                    value 3.0  x weight -0.008 = -0.0240 (penalty, verifiable)
  category affinity        value 0.2  x weight +0.040 = +0.0080 (19% of score, verifiable)
  similar users bought     value 0.9  x weight +0.022 = +0.0198 (47% of score, unverifiable)
  you viewed this category value 0.4  x weight +0.035 = +0.0140 (33% of score, verifiable)

reading: the largest contribution is 'similar users bought', which the
user cannot check - no record of similar users exists on their
side. The verifiable claims ('you viewed this category',
'category affinity') are smaller. Trust is built on explanations
the user can falsify, not on the term with the largest coefficient.
```

## Notes

- The largest contribution (47%) is 'similar users bought', which the user cannot check; the verifiable claims are smaller.
- Trust is built on explanations the user can falsify, not on the term with the largest coefficient.
