# Run — the vocabulary mismatch that cuts the candidate, read

**Date:** 2026-08-07
**Command:** `uv run python core/lexical_gap_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** under one second.
**Cost:** \$0 (local lane).

## Purpose

Measure the harder half of the stage-11 vocabulary-mismatch failure: a
relevant document that shares no query term scores 0.0000 and is cut
before ranking, and measure the synonym-expansion fix plus its precision
cost.

## Output

```
vocabulary mismatch, read — the cut before ranking:
  query 'cheap headphones' (unexpanded):
    doc7   1.6952  cheap running shoes on sale
    doc1   0.8371  wireless headphones noise cancelling bluetooth
    doc5   0.8371  headphones price comparison review 2026
    doc2   0.7690  over ear headphones comfortable long battery
    doc3   0.0000  running shoes lightweight breathable
    recall@3 = 0.00  (doc6 scored 0.0000)

  fix: expand 'cheap' with its synonyms 'affordable budget':
    doc6   3.3903  affordable earbuds budget friendly sound  <-- relevant, recovered
    doc7   1.6952  cheap running shoes on sale
    doc1   0.8371  wireless headphones noise cancelling bluetooth
    doc5   0.8371  headphones price comparison review 2026
    doc2   0.7690  over ear headphones comfortable long battery
    recall@3 = 1.00

  trade: the broader query also matches 'cheap running shoes'
  (doc7) — expansion raised the candidate count and pulled in
  a false positive for headphones. Recall is fixed; precision
  must be re-checked, which is what reranking is for.
```

## Notes

- The unexpanded query's relevant doc6 is not even in the printed top-5:
  it ties at 0.0000 and sorts below doc3. The cut is absolute — a
  zero-scoring document is not ranked worse, it is absent.
- Expansion recovers recall@3 from 0.00 to 1.00 but adds doc7 as a
  false positive for headphones; the trade is the stage's own claim
  (retrieval widens, ranking re-orders), which is why stages 19-21 carry
  expansion and fusion as their own audits.
