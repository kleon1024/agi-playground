# Run — the logit-level equality, read from the recorded streaming run

**Date:** 2026-08-06
**Command:** `uv run python core/logit_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the committed JSON).
**Cost:** \$0 (local lane; the streaming run was the stage's recorded
2026-07-31).

## Purpose

Stage 01 claims cached decode equals full recompute, checked at logit
level. This run reads the JSON and lays out the gap numbers.

## Output

```
  clips matched: 30/30
  max logit gap: 1.19e-05
  mean logit gap: 5.27e-06
```

## Notes

- Identical tokens could hide a confidence shift, so the check is at logit
  level — a max gap of 1e-5 is machine noise, not similarity.
- The zero quality gap is what makes the latency win a pure win rather
  than a different model.
