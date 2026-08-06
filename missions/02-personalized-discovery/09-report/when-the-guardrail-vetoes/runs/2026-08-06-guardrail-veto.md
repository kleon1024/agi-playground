# Run — the guardrail that vetoes a headline, read from the fixture

**Date:** 2026-08-06
**Command:** `uv run python core/guardrail_veto.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.01s (reads the committed fixture).
**Cost:** \$0 (local lane).

## Purpose

Stage 09's breached fixture is the report stage's sharpest lesson: a
candidate that beats both baselines by more than seed variance can still be
NOT MET. This run reads the fixture and puts the headline beside the veto.

## Output

```
the breached fixture, read:
  candidate nDCG@10: 0.4102  vs popularity 0.3012 / CF 0.3552
  -> beats both baselines by more than seed variance
  cold-start guardrail: candidate 0.271 < baseline 0.298  -> BREACH

reading: a guardrail is a veto, not an extra point — a headline
win with one breached guardrail still renders NOT MET.
```

## Notes

- The fixture is explicitly synthetic and illustrative; it exists to show
  the report format and the veto rule, not a mission result.
- The breach is on cold-start coverage — the guardrail that protects the
  new users personalization is supposed to help. A system that improves
  the average while taxing new users is exactly what the guardrail exists
  to reject.
