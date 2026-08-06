# Run — the click as a label, executed on the bias model

**Date:** 2026-08-06
**Command:** `uv run python core/click_label_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s.
**Cost:** \$0 (local lane).

## Purpose

Clicks are not relevance: position itself drives exposure. This run
quantifies the bias with an exposure model.

## Output

```
  observed clicks = relevance x exposure:
    pos 1 item A: observed 0.80 (relevance 0.8 x exposure 1.0)
    pos 2 item B: observed 0.30 (relevance 0.6 x exposure 0.5)
    pos 3 item C: observed 0.10 (relevance 0.4 x exposure 0.25)
```

## Notes

- The same item clicked more at pos 1 than pos 3 is exposure, not
  relevance; a ranker trained on raw clicks learns to put anything at the
  top.
- Correcting the bias (e.g. inverse-propensity weighting) is what makes
  clicks usable as relevance labels.
