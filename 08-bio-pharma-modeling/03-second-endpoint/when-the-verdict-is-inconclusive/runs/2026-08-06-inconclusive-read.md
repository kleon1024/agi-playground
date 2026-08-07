# Run — the inconclusive verdict, read from the recorded second-endpoint seeds

**Date:** 2026-08-06
**Command:** `uv run python core/inconclusive_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads six committed seed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-01
runs).

## Purpose

Stage 03's NR-PPAR-gamma result is a no-result: the model's nominal lead
sits inside its own seed spread. This run reads the committed seeds and
lays out the means, spreads, and the verdict rule.

## Output

```
NR-PPAR-gamma, second endpoint, read from the recorded seeds:
  descriptor: [0.653, 0.6575, 0.6558]  mean 0.6554 spread 0.0044
  model:      [0.6956, 0.6337, 0.648]  mean 0.6591 spread 0.0620
  gap (model - descriptor): +0.0037  vs larger spread 0.0620
  -> INCONCLUSIVE: the gap is ~1/17th of the model's own spread,
     a no-result by the rule mission.yaml declared before any code.
```

## Notes

- The trained model's spread (0.0620) is ~14x the descriptor baseline's
  (0.0044) on the same architecture and step count — scarcity amplifies
  seed randomness, which is the measurable cause of the no-result.
- INCONCLUSIVE is a third, legitimate outcome the mission's framing allows:
  it neither replicates nor reverses stage 02's SR-MMP finding.
