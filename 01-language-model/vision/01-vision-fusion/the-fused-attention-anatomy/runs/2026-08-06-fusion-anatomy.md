# Run — the fused-attention anatomy, computed from the stage-01 config

**Date:** 2026-08-06
**Command:** `uv run python core/fusion_anatomy.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.01s (arithmetic over the measured config).
**Cost:** \$0 (local lane; the parameters are the stage's recorded
2026-07-31 totals).

## Purpose

The vision pathway's structure is the surprise: there is no separate
cross-attention module. This run computes the mask quadrants and the
parameter delta from the measured stage-01 configuration.

## Output

```
fused-attention mask anatomy (stage-01 config), computed:
  sequence: 64 vision tokens + 8 text tokens = 72
  quadrant  vision->vision  vision->text  text->vision  text->text
  mask      bidirectional  blocked       full          causal
  parameters: vision 732,928 vs text-only 718,464 (+14,464)
```

## Notes

- The image enters as a prefix: vision tokens attend bidirectionally, text
  sees the whole image, text stays causal — four quadrants in one shared
  attention block.
- The only new mechanism is the patch embedding plus the fused mask
  (+14,464 parameters), which is why mission 05 claims reuse, not rewrite.
