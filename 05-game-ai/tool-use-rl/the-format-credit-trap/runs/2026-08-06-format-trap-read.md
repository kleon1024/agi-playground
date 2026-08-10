# Run — the format-credit trap, read from the recorded tool-use RL seeds

**Date:** 2026-08-06
**Command:** `uv run python core/format_trap_read.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three committed seed JSONs).
**Cost:** \$0 (local lane; the training was the stage's recorded 2026-08-03
runs).

## Purpose

Stage 06's reward splits format credit from outcome credit. This run reads
the recorded seeds and lays out what the policy learned per level.

## Output

```
  seed 0: mean reward 0.884 | level-1 answer_rate 1.00 | level-5 tool_rate 1.00
  seed 1: mean reward 0.743 | level-1 answer_rate 1.00 | level-5 tool_rate 0.00
  seed 2: mean reward 0.759 | level-1 answer_rate 1.00 | level-5 tool_rate 0.00
```

## Notes

- The policy answers easy levels directly (answer_rate 1.00 at level 1 in
  every seed), but only seed 0 pays for the tool at the hard level.
- Seeds 1-2 stop paying for the tool — the tool-rate collapse the mission
  records in its two-seeds detour.
