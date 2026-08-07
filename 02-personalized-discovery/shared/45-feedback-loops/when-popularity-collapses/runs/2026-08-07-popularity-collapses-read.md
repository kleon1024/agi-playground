# Run — when popularity collapses, executed on the world-change read

**Date:** 2026-08-07
**Command:** `uv run python core/popularity_collapses.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.04s.
**Cost:** \$0 (local lane).

## Purpose

Stage 45's detour: at round 150 a starved item's true CTR jumps above the
head. This run reads whether the loop ever notices.

## Output

```
popularity collapses, read (item 15's true ctr jumps at round 150):
  item 15 impressions share: 0.1%
  head 5 impressions share at round 300: 99%

reading: item 15 became the best item at round 150, and by
round 300 it holds a sliver of exposure. The loop cannot
discover a winner it never shows; 'more of what works'
works until the world changes, and the collapse is the
cost of entrenchment. Exploration is the repair, and it
must be budgeted before the change, not after.
```

## Notes

- Item 15 became the best item at round 150, and by round 300 it holds 0.1% of exposure.
- Exploration is the repair, and it must be budgeted before the change, not after.
