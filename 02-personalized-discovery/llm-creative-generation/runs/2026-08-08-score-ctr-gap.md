# Run — surface score versus measured CTR, which creative wins

**Date:** 2026-08-08
**Command:** `uv run python core/score_ctr_gap.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.12.9 via uv; stdlib only.
**Wall-clock:** 0.1s.
**Cost:** \$0 (local lane).

## Purpose

Stage 41's executed draw generates variants, scores them on the surface,
and delivers the surface winner. This audit asks the industrial question
that single scored batch skips: the surface score (urgency, buzzwords,
appearance) is not the measured CTR the delivery earns, and the two pick
different winners. It draws 5,000 batches of 10 generated variants, gives
each a surface score that mixes 60 percent true-signal proxy with 40
percent appeal junk that predicts nothing, and measures how often the
surface-selected creative is not the CTR-best one, plus what the selection
costs in expected delivered CTR.

## Output

```
score-versus-CTR gap, audited: does the surface pick convert?
  one illustrative batch of 10 generated variants
  surface score = 60% true-signal proxy + 40% appeal junk

  variant      | surface score | true CTR
  variant 1    |    0.446      | 0.0178
  variant 2    |    0.567      | 0.0776
  variant 3    |    0.492      | 0.0521
  variant 4    |    0.717      | 0.0669 <- selected
  variant 5    |    0.095      | 0.0139
  variant 6    |    0.679      | 0.0844
  variant 7    |    0.465      | 0.0774
  variant 8    |    0.572      | 0.0473
  variant 9    |    0.539      | 0.0267
  variant 10   |    0.556      | 0.0906 <- CTR best

  surface-selected: variant 4 (CTR 0.0669)
  CTR-best:         variant 10 (CTR 0.0906)

  over 5,000 batches of 10 variants:
    surface selection != CTR best:  55.1%
    mean relative CTR loss:          7.3%
    mean chosen CTR vs best CTR:   0.0848 vs 0.0914

reading: with a surface-appeal component of 0.40, the
surface score picks the CTR-best creative in only about
half the batches, and the selection gives up a slice of
delivered CTR every time it misses. The score has to be
calibrated against measured delivery before it decides —
stage 16's pCTR rule applied to the creative surface.
```

## Notes

- 5,000 fixed-seed batches (seed 11) of 10 variants each; the displayed
  illustrative batch uses seed 1 so the miss is visible in one reading.
- Surface score mixes a 0.60-weight normalized true-CTR proxy with a
  0.40-weight uniform appeal component that carries no signal.
- With that appeal junk, the surface selection misses the CTR-best
  creative on 55.1 percent of batches and gives up 7.3 percent mean
  relative CTR; chosen CTR averages 0.0848 against a 0.0914 best.
- The score is only a delivery prediction when it is calibrated on
  measured CTR, the same discipline stage 16 applies to pCTR ranking;
  otherwise the creative team tunes a score that does not predict
  what the delivery loop pays for.
