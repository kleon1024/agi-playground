# Run — cold-start severity vs baseline success, three environments

**Date:** 2026-08-06
**Command:** `uv run python core/cold_start_sparsity.py`
**Hardware:** Apple M1 Pro, macOS 15.6.1, CPU-only.
**Software:** Python 3.11.14 via uv; stdlib only.
**Wall-clock:** 0.02s (reads three recorded minigrid JSONs + cited
baselines).
**Cost:** \$0 (local lane).

## Purpose

Mission 06's three environments give a measured gradient in cold-start
severity. This run assembles the recorded baseline-success and
GRPO-degeneracy numbers into the table that explains the pattern.

## Output

```
environment                 random baseline  degenerate steps
mission 01 arithmetic          ~0% (format)           200/200
mission 06 grid-world                 22.2%             1/200
mission 06 MiniGrid            0.4% (2/500)      [80, 80, 80]
```

## Notes

- Degeneracy tracks baseline success: grid-world's 22.2% random success
  gives the group statistic enough variance to move (1/200 degenerate);
  MiniGrid's 0.4% gives it almost none (80/80 degenerate per seed); mission
  01's near-zero format rate gives it none at all (200/200).
- The mechanism is the group-relative advantage: it needs reward variance
  inside each rollout group, and variance requires a policy that sometimes
  succeeds. A near-zero baseline is a total cold start by construction, not
  a training failure.
