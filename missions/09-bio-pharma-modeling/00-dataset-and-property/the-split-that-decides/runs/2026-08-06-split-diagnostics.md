# Run — scaffold-split label shift, three endpoints

**Date:** 2026-08-06
**Command:** `uv run python core/split_diagnostics.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three recorded split summaries).
**Cost:** \$0 (local lane).

## Purpose

The scaffold split guarantees no scaffold crosses train/test (checked in the
stage 00 run record: 1,668 scaffolds, 507 train scaffolds, zero overlap).
But splitting by scaffold can still shift the label distribution, because
scaffolds cluster by activity. This run lays out that shift across the three
endpoints beside the recorded verdicts.

## Output

```
endpoint          train+   test+  shift pp  verdict
SR-MMP             14.8%   19.7%     +4.9pp  descriptor wins beyond spread
NR-PPAR-gamma       2.3%    5.3%     +3.0pp  inconclusive (gap inside spread)
NR-ER              12.7%   13.2%     +0.5pp  descriptor wins beyond spread
```

## Notes

- Every endpoint's test set is MORE positive than its train set: the
  scaffold split systematically hands the test side a harder class balance.
  The shift is 0.5-4.9 percentage points depending on the endpoint.
- The largest shift sits on the scarcest endpoint: NR-PPAR-gamma's test
  positive rate (5.3%) is 2.3x its train's (2.3%), and that endpoint is the
  one whose verdict is inconclusive — the label shift and the variance
  story the mission's stage 05 names are the same confound.
- The verdicts (descriptor wins on SR-MMP and NR-ER, inconclusive on
  NR-PPAR-gamma) live inside these shifts; the chapter reads the split as a
  real, measured confound the comparisons sit inside.
