# Run — LLM creative generation, executed on the generate-then-select model

**Date:** 2026-08-07
**Command:** `uv run python core/generated_creative.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 41 asks how an LLM produces ad creative. This run generates four variants, scores them, and selects one before delivery.

## Output

```
llm creative generation, read:
  0.08  v1: 'Run faster, pay less'
  0.06  v2: 'Marathon shoes, 20% off'
  0.04  v3: 'New season, new pace'
  0.02  v4: 'Buy now'
  selected: v1: 'Run faster, pay less'

reading: generation is cheap, impressions are not — the LLM
produces variants and a scoring model picks before delivery.
The frontier risk is collapse (identical variants) and surface
scoring that misses real CTR, which the detours price.
```

## Notes

- Generation is cheap, impressions are not — the LLM produces variants and a scoring model picks before delivery.
- The frontier risk is collapse (identical variants) and surface scoring that misses real CTR, which the detours price.
