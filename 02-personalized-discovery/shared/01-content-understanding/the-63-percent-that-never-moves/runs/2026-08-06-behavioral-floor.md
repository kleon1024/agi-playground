# Run — the behavioural floor that never moves, read from the recorded sweep

**Date:** 2026-08-06
**Command:** `uv run python core/behavioral_floor.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads the recorded run markdown).
**Cost:** \$0 (local lane; the sweep was the stage's recorded run).

## Purpose

Stage 01's threshold sweep shows behavioural coverage constant at 63%. This
run reads the record and isolates that constant from the threshold dial.

## Output

```
  catalogue: 300 items, 112 cold
  behavioural coverage: 63% at every threshold
  union/cold coverage move with the threshold; behaviour does not
```

## Notes

- The content queue's boundary is a dial (union 100% -> 72%, cold 100% ->
  25%); the behaviour queue's reach is a fact about the log (63%, fixed).
- A threshold can never rescue an item neither queue reaches.
