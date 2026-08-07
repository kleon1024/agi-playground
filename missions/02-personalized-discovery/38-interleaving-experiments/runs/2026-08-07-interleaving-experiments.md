# Run — interleaving experiments, executed on the blended-list credit model

**Date:** 2026-08-07
**Command:** `uv run python core/interleave_read.py`
**Hardware:** Apple M1 Pro, macOS, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.03s.
**Cost:** \$0 (local lane).

## Purpose

Stage 38 asks how to compare two rankings with far fewer users. This run interleaves two teams' lists and credits the clicks.

## Output

```
interleaving, read:
  team_a: ['d1', 'd2', 'd3']
  team_b: ['d4', 'd2', 'd5']
  interleaved: ['d1', 'd4', 'd2', 'd3', 'd5']
  clicks: ['d4', 'd2']
  credit: team_a 1, team_b 2

reading: both users see one blended list, and clicks credit
the team that proposed each clicked result. Team b wins here
because d4 is its exclusive proposal. Interleaving needs far
fewer users than a between-user A/B, which is why online teams
use it for ranking changes.
```

## Notes

- Both users see one blended list; clicks credit the team that proposed each clicked result.
- Interleaving needs far fewer users than a between-user A/B, which is why online teams use it for ranking changes.
