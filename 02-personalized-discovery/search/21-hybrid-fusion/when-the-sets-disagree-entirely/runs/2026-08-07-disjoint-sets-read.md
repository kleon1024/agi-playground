# Run — the sets that disagree entirely

**Date:** 2026-08-07
**Command:** `uv run python core/disjoint_sets.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Show what reciprocal rank fusion produces when the two matcher sets are
disjoint: no agreement to reward, so the fused order is an interleave
of two priors and the top of the page is decided by a coin flip.

## Output

```
disjoint sets, read (reciprocal rank fusion):
  d1: 0.0164 (lexical)
  d5: 0.0164 (dense)
  d2: 0.0161 (lexical)
  d6: 0.0161 (dense)
  d3: 0.0159 (lexical)
  d7: 0.0159 (dense)
  d4: 0.0156 (lexical)
  d8: 0.0156 (dense)
  fused top-2: ['d1', 'd5']

reading: no document appears in both sets, so fusion has
nothing to reward — every score is a single matcher's rank
contribution. The fused top is a tie between the two rank-1s
(both 1/61) and the page order is a coin flip between the
lexical prior and the dense prior, not a relevance decision.
```

## Notes

- The fused list interleaves the two matchers one-for-one: the two
  rank-1 documents tie at 1/61 each, so the page top between them is
  arbitrary.
- RRF's signal is agreement: Cormack, Clarke and Büttcher, "Reciprocal
  Rank Fusion Outperforms Condorcet and Individual Rank Learning
  Methods", SIGIR 2009, show RRF rewarding documents several rankings
  place highly. With disjoint sets that signal is empty.
- The operational check is the served overlap rate. When it collapses,
  one matcher silently failed on the query (vocabulary gap or sparse
  tail) and fusion papered over it with an interleaving.
