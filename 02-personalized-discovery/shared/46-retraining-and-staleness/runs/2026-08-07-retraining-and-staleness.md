# Run — retraining and staleness, executed on the aging-snapshot model

**Date:** 2026-08-07
**Command:** `uv run python core/staleness.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 46 introduces staleness. This run evaluates an hour-0 model and an
hour-6 model against the truth at later hours, counting pairwise rank
errors.

## Output

```
staleness, read (pairwise rank errors vs the truth at hour h):
  snapshot from hour 0 evaluated at hour h:
    hour  0: 0 wrong pairs
    hour  6: 5 wrong pairs
    hour 12: 6 wrong pairs
  snapshot from hour 6 evaluated at hour 12:
    hour 12: 1 wrong pairs

reading: rank error grows from 0 at hour 0 to several
wrong pairs at hour 12. A snapshot from hour 6 cuts that
error to a single pair.
The question is not whether to retrain - the world moves -
but how to notice that the snapshot has stopped paying.
```

## Notes

- Rank error grows from 0 at hour 0 to 6 wrong pairs at hour 12; the hour-6 snapshot cuts it to 1 pair at hour 12.
- The question is not whether to retrain — the world moves — but how to notice that the snapshot has stopped paying.
