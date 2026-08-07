# Run — generative retrieval, executed on the beam decode over doc IDs

**Date:** 2026-08-07
**Command:** `uv run python core/genret_read.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 35 asks whether a model can emit document IDs directly. This run decodes a beam over four document IDs and reads the top-2.

## Output

```
generative retrieval, read (beam over doc IDs):
  doc_17: 0.9
  doc_03: 0.7
  doc_42: 0.4
  doc_09: 0.2
  beam top-2: ['doc_17', 'doc_03']

reading: the model emits the doc IDs directly, so there is no
index scan and no candidate generation step. The frontier cost
is decode latency and the risk of emitting IDs that do not
exist — the hallucination detour prices that.
```

## Notes

- The model emits doc IDs directly: no index scan, no candidate generation step.
- The frontier cost is decode latency and the risk of emitting IDs that do not exist — the hallucination detour prices that.
