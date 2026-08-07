# Run — benchmark contamination, detection methods vs a leaked eval set

**Date:** 2026-08-07
**Command:** `uv run python core/contamination_check.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 7s (200-item benchmark, 60 leaked docs at three edit
levels, 400 background docs, four detectors, two recovery levels).
**Cost:** \$0 (local lane).

## Purpose

Stage 00's release record names contamination checks as a required item.
This run executes them: a synthetic benchmark of 200 question-answer
items, 60 of which leak into a 460-document corpus at three edit levels
(20 verbatim copies, 20 near copies at measured Jaccard 0.57, 20
paraphrases), and four detectors read against the leak. The inflation
pass then asks how many benchmark answers the corpus teaches at all —
the memorization measure of Carlini et al. 2021.

## Output

```
benchmark contamination, read (detection + inflation):
  benchmark items: 200; leaked into corpus: 60 (20 exact / 20 near / 20 paraphrase)
  near-edit Jaccard ~0.57; paraphrase Jaccard ~0.00

  detection rate (hit/total):
    exact hash   exact 20/20  near 4/20  paraphrase 0/20  background fp 0/400
    13-gram      exact 20/20  near 19/20  paraphrase 0/20  background fp 0/400
    minhash 0.7  exact 20/20  near 13/20  paraphrase 0/20  background fp 0/400
    minhash 0.5  exact 20/20  near 17/20  paraphrase 0/20  background fp 0/400

  benchmark answers the corpus teaches:
    strong signal (subject + 'answer:' + property in one doc):
      clean corpus:        0/200
      contaminated corpus: 40/200
    fact-level (subject + property co-occur):
      clean corpus:        0/200
      contaminated corpus: 60/200
```

## Notes

- The 13-gram overlap heuristic (Brown et al. 2020, GPT-3) is the
  workhorse: it catches 20/20 verbatim and 19/20 near copies with zero
  background false positives. Exact hashing catches only verbatim copies
  (and the four near copies that happened to render identically), and
  MinHash near-duplicate detection is a recall dial: 13/20 near copies
  at a 0.7 Jaccard verification threshold, 17/20 at 0.5, with zero
  background false positives either way.
- The paraphrase is the dangerous leak: 0/20 across every detector, yet
  its 20 answers are all teachable from the corpus (fact-level recovery
  60/200 vs strong-signal 40/200). Detection is layered, never single;
  the release gate runs the checks before training, and residual overlap
  is disclosed rather than silently re-run after the score is known.
- The clean corpus teaches 0/200 answers at either level: the 
  background documents share the vocabulary but no benchmark pairing.

## Evidence boundary

Synthetic and deterministic (single seed). It demonstrates detection
rates and the inflation mechanism, not production overlap rates — those
come from running the same four checks against the real eval sets and
the real corpus before release.
